from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class FeedbackCategory(StrEnum):
    overall = "overall"
    reference_resolution = "reference_resolution"
    claim_span = "claim_span"
    source_evidence = "source_evidence"
    relation = "relation"
    transformation = "transformation"
    missing_evidence = "missing_evidence"
    nuance = "nuance"
    explanation = "explanation"
    access = "access"
    other = "other"

class FeedbackSubmission(BaseModel):
    workspace_id: UUID
    actor_user_id: UUID | None = None
    evidence_link_id: UUID
    category: FeedbackCategory
    proposed_relation: str | None = None
    proposed_source_span: dict[str, Any] | None = None
    comment: str | None = None
    idempotency_key: str

class FeedbackRecord(BaseModel):
    id: UUID
    workspace_id: UUID
    actor_user_id: UUID | None
    evidence_link_id: UUID
    category: FeedbackCategory
    proposed_relation: str | None
    proposed_source_span: dict[str, Any] | None
    comment: str | None
    created_at: datetime
    idempotency_key: str

class AdjudicationItem(BaseModel):
    id: UUID
    priority_score: float
    evidence_link_id: UUID
    category: FeedbackCategory
    reported_issue_count: int
    created_at: datetime
