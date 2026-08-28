from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .enums import AnalysisMode, AnalysisStatus, Audience, EvidenceLinkStatus, EvidenceRelation


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WholeDocumentScope(StrictModel):
    kind: Literal["whole_document"] = "whole_document"


class CitationAnchorsScope(StrictModel):
    kind: Literal["citation_anchors"]
    citation_anchor_ids: list[UUID] = Field(min_length=1)


AnalysisScope = Annotated[WholeDocumentScope | CitationAnchorsScope, Field(discriminator="kind")]


class AnalysisCreateRequest(StrictModel):
    workspace_id: UUID
    document_id: UUID
    mode: AnalysisMode
    scope: AnalysisScope
    audience: Audience
    source_policy_profile: str = Field(min_length=1, max_length=100)


class AnalysisProgress(StrictModel):
    stage: AnalysisStatus
    completed_units: int = Field(ge=0)
    total_units: int = Field(ge=0)
    percent: float = Field(ge=0, le=100)


class Limitation(StrictModel):
    code: str
    message: str
    reference_entry_id: UUID | None = None
    recoverable_actions: list[str] = Field(default_factory=list)


class AnalysisLinks(StrictModel):
    self: str
    stream: str
    evidence_links: str


class Analysis(StrictModel):
    id: UUID
    workspace_id: UUID
    document_id: UUID
    status: AnalysisStatus
    mode: AnalysisMode
    audience: Audience
    progress: AnalysisProgress
    limitations: list[Limitation] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    links: AnalysisLinks

    @classmethod
    def create(cls, request: AnalysisCreateRequest) -> "Analysis":
        analysis_id = uuid4()
        now = datetime.now(UTC)
        base = f"/v1/analyses/{analysis_id}"
        return cls(
            id=analysis_id,
            workspace_id=request.workspace_id,
            document_id=request.document_id,
            status=AnalysisStatus.CREATED,
            mode=request.mode,
            audience=request.audience,
            progress=AnalysisProgress(
                stage=AnalysisStatus.CREATED,
                completed_units=0,
                total_units=0,
                percent=0,
            ),
            created_at=now,
            updated_at=now,
            links=AnalysisLinks(
                self=base,
                stream=f"{base}/stream",
                evidence_links=f"{base}/evidence-links",
            ),
        )


class EvidenceLinkSummary(StrictModel):
    id: UUID
    status: EvidenceLinkStatus
    evidence_relation: EvidenceRelation
    headline: str


class EvidenceLinkPage(StrictModel):
    items: list[EvidenceLinkSummary] = Field(default_factory=list)
    next_cursor: str | None = None


class HealthResponse(StrictModel):
    status: Literal["ok"] = "ok"
    service: Literal["citetrace-api"] = "citetrace-api"
    version: str


class ProblemDetails(StrictModel):
    type: HttpUrl | str = "about:blank"
    title: str
    status: int
    detail: str
    code: str
    instance: str | None = None
    trace_id: str = Field(default_factory=lambda: uuid4().hex)
    retryable: bool = False
