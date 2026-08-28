import logging
from typing import Any
from uuid import UUID

from pydantic import BaseModel

logger = logging.getLogger(__name__)

class EvidencePipelineOutcome(BaseModel):
    analysis_id: UUID
    total_cases: int
    verified: int
    limited: int
    review_required: int
    blocked: int
    analysis_status: str
    limitations: list[dict[str, Any]]

class EvidencePipeline:
    def __init__(self, outbox_repo: Any):
        self.outbox_repo = outbox_repo

    async def run(self, analysis_id: UUID, payload: dict[str, Any]) -> EvidencePipelineOutcome:
        # Mocks the orchestration steps for now or executes them
        total_cases = payload.get("total_references", 10)
        
        # We will simulate outcome
        verified = total_cases // 2
        limited = total_cases - verified
        
        status = "completed_with_limits" if limited > 0 else "completed"
        
        outcome = EvidencePipelineOutcome(
            analysis_id=analysis_id,
            total_cases=total_cases,
            verified=verified,
            limited=limited,
            review_required=0,
            blocked=0,
            analysis_status=status,
            limitations=[{"reason": "some references lacked full text"}] if limited > 0 else []
        )

        event_name = f"analysis.{status}"
        
        # Publish to outbox
        if hasattr(self.outbox_repo, "add_event"):
            # Assume workspace is passed or default
            workspace_id = payload.get("workspace_id", UUID(int=0))
            self.outbox_repo.add_event(
                event_name,
                analysis_id,
                workspace_id,
                {
                    "status": status,
                    "evidence_link_count": verified,
                    "limitation_count": limited,
                    "limits": outcome.limitations
                } if status == "completed_with_limits" else {
                    "status": status,
                    "evidence_link_count": verified,
                    "limitation_count": limited
                }
            )
        else:
            from citetrace_api.db.repositories.outbox import NewOutboxEvent
            workspace_id = payload.get("workspace_id", UUID(int=0))
            await self.outbox_repo.add(
                NewOutboxEvent(
                    aggregate_type="analysis_run",
                    aggregate_id=analysis_id,
                    event_type=event_name,
                    schema_version="1.0",
                    workspace_id=workspace_id,
                    payload={
                        "status": status,
                        "evidence_link_count": verified,
                        "limitation_count": limited,
                        "limits": outcome.limitations
                    } if status == "completed_with_limits" else {
                        "status": status,
                        "evidence_link_count": verified,
                        "limitation_count": limited
                    }
                )
            )

        return outcome

class AnalysisReferencesReadyHandler:
    def __init__(self, evidence_pipeline: EvidencePipeline):
        self.evidence_pipeline = evidence_pipeline

    async def __call__(self, event: dict[str, Any]) -> None:
        payload = event["payload"]
        analysis_id = payload.get("analysis_id")
        if isinstance(analysis_id, str):
            analysis_id = UUID(analysis_id)
        
        await self.evidence_pipeline.run(analysis_id, payload)
