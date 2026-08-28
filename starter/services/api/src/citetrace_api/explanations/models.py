from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ExplanationStatementKind(StrEnum):
    EVIDENCE_BASED = "evidence_based"
    INFERENCE = "inference"
    LIMITATION = "limitation"
    INSTRUCTION = "instruction"

class ExplanationStatement(BaseModel):
    kind: ExplanationStatementKind
    text: str
    supporting_citing_span_ids: tuple[UUID, ...] = Field(default_factory=tuple)
    supporting_source_span_ids: tuple[UUID, ...] = Field(default_factory=tuple)
    confidence: float
    display_order: int

    @model_validator(mode="after")
    def validate_evidence_based(self) -> Self:
        if self.kind == ExplanationStatementKind.EVIDENCE_BASED and not self.supporting_source_span_ids:
            raise ValueError("evidence_based statement MUST have >= 1 supporting source span ID.")
        return self

class ExplanationDraft(BaseModel):
    statements: list[ExplanationStatement]
    summary_text: str
    audience: str
    mode: str
