from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class ReadingPriorityBand(StrEnum):
    MUST_READ = "must_read"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ReadingPriority(BaseModel):
    analysis_id: UUID
    reference_entry_id: UUID
    mode: str
    score: float
    band: ReadingPriorityBand
    reason_codes: tuple[str, ...]
    recommended_sections: tuple[str, ...]
    next_actions: tuple[str, ...]
    feature_profile_version: str

class ReferencePriorityInput(BaseModel):
    reference_entry_id: UUID
    local_label: str
    raw_reference: str
    parsed_title: str | None = None
    resolution_status: str
    citation_intents: tuple[str, ...]
    evidence_relations: tuple[str, ...]
    transformations: tuple[str, ...]
    access_level: str
    section_distribution: dict[str, int]
    in_text_citation_count: int
