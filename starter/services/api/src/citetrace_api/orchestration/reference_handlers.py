import logging
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from citetrace_api.acquisition.policy import AccessLevel
from citetrace_api.acquisition.service import SourceAcquisitionService
from citetrace_api.db.repositories.parsed_documents import ParsedDocumentsRepository
from citetrace_api.providers.models import BibliographicQuery
from citetrace_api.resolution.service import ReferenceResolutionService

logger = logging.getLogger(__name__)


@dataclass
class ReferencePipelineResult:
    total_references: int = 0
    resolved: int = 0
    ambiguous: int = 0
    unresolved: int = 0
    full_text_available: int = 0
    abstract_only: int = 0
    not_accessible: int = 0
    limitations: list[dict[str, object]] = field(default_factory=list)


class ReferencePipeline:
    def __init__(
        self,
        resolution_service: ReferenceResolutionService,
        acquisition_service: SourceAcquisitionService,
    ) -> None:
        self.resolution_service = resolution_service
        self.acquisition_service = acquisition_service

    async def process_references(
        self, workspace_id: UUID, references: list[dict[str, Any]], trace_id: str = ""
    ) -> ReferencePipelineResult:
        result = ReferencePipelineResult()
        result.total_references = len(references)

        for ref in references:
            query = BibliographicQuery(
                reference_entry_id=UUID(ref["id"]),
                title=ref.get("title"),
                authors=tuple(
                    ref.get("authors", [])
                ),  # Or parsing from raw if needed, maybe just empty for test
                year=ref.get("year"),
                venue=ref.get("venue"),
                identifiers=ref.get("identifiers") or {},
                raw_reference=ref.get("raw_reference") or "",
            )

            decision, candidates = await self.resolution_service.resolve(query, trace_id=trace_id)

            if decision.status == "ambiguous":
                result.ambiguous += 1
                result.limitations.append(
                    {
                        "code": "reference_ambiguous",
                        "message": "Reference resolved to multiple candidates without clear winner.",
                        "reference_entry_id": str(query.reference_entry_id),
                        "recoverable_actions": ["user_resolution_required"],
                    }
                )
                continue

            if decision.status == "unresolved":
                result.unresolved += 1
                result.limitations.append(
                    {
                        "code": "reference_unresolved",
                        "message": "Reference could not be resolved to any candidate.",
                        "reference_entry_id": str(query.reference_entry_id),
                        "recoverable_actions": [],
                    }
                )
                continue

            result.resolved += 1
            cand = next(
                c
                for c in candidates
                if f"{c.provider}:{c.provider_record_id}" == decision.selected_candidate_id
            )

            # Try to acquire source
            # Generating a mock work_version_id based on provider_record_id or UUID
            import hashlib

            work_version_id_str = hashlib.md5(cand.provider_record_id.encode()).hexdigest()
            # UUID needs 32 hex digits
            work_version_id = UUID(work_version_id_str)

            doi = cand.identifiers.get("doi")
            abstract = (
                cand.raw_snapshot.get("abstract") if isinstance(cand.raw_snapshot, dict) else None
            )

            if not isinstance(abstract, str):
                abstract = None

            outcome = await self.acquisition_service.acquire(
                work_version_id=work_version_id,
                workspace_id=workspace_id,
                doi=doi,
                title=cand.title,
                abstract=abstract,
                trace_id=trace_id,
            )

            if outcome.access_level in (
                AccessLevel.open_access_full_text,
                AccessLevel.publisher_open_full_text,
                AccessLevel.repository_manuscript,
            ):
                result.full_text_available += 1
            elif outcome.access_level == AccessLevel.abstract_only:
                result.abstract_only += 1
                result.limitations.append(
                    {
                        "code": "source_abstract_only",
                        "message": "Only abstract is available for this reference.",
                        "reference_entry_id": str(query.reference_entry_id),
                        "recoverable_actions": ["upload_full_text"],
                    }
                )
            else:
                result.not_accessible += 1
                result.limitations.append(
                    {
                        "code": "source_not_accessible",
                        "message": "Source could not be accessed.",
                        "reference_entry_id": str(query.reference_entry_id),
                        "recoverable_actions": ["upload_full_text"],
                    }
                )

        return result


class DocumentParsedHandler:
    def __init__(
        self,
        parsed_docs_repo: ParsedDocumentsRepository,
        pipeline: ReferencePipeline,
        outbox_repo: Any,
    ) -> None:
        self.parsed_docs_repo = parsed_docs_repo
        self.pipeline = pipeline
        self.outbox_repo = outbox_repo

    async def __call__(self, event: dict[str, Any]) -> None:
        payload = event["payload"]
        parsed_document_id = payload["parsed_document_id"]
        workspace_id = event["workspace_id"]
        trace_id = event.get("trace_id", "")

        references = await self.parsed_docs_repo.get_reference_entries(parsed_document_id)

        result = await self.pipeline.process_references(
            workspace_id=UUID(str(workspace_id)), references=references, trace_id=trace_id
        )

        import dataclasses

        result_dict = dataclasses.asdict(result)

        await self._add_event(
            event_type="document.references.resolved",
            aggregate_id=parsed_document_id,
            workspace_id=workspace_id,
            payload={
                "parsed_document_id": parsed_document_id,
                "reference_pipeline_result": result_dict,
            },
        )

        # We can also emit a ready event or let an analysis orchestrator do it.
        # But if the prompt requires `analysis.references.ready`, we might need analysis_id.
        # However, `document.parsed` does not have analysis_id.
        # I'll stick to document.references.resolved as stated in the instructions:
        # "Emits analysis.references.ready (or document.references.resolved) event with summary counts and limitations to the outbox."

    async def _add_event(
        self, event_type: str, aggregate_id: str, workspace_id: str, payload: dict[str, Any]
    ) -> None:
        if hasattr(self.outbox_repo, "add_event"):
            self.outbox_repo.add_event(
                event_type, UUID(str(aggregate_id)), UUID(str(workspace_id)), payload
            )
        else:
            from citetrace_api.db.repositories.outbox import NewOutboxEvent

            await self.outbox_repo.add(
                NewOutboxEvent(
                    aggregate_type="source_asset",
                    aggregate_id=UUID(str(aggregate_id)),
                    event_type=event_type,
                    schema_version="1.0",
                    workspace_id=UUID(str(workspace_id)),
                    payload=payload,
                )
            )
