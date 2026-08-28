from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class EvidenceLinkStatus(StrEnum):
    VERIFIED = "verified"
    LIMITED = "limited"
    REVIEW_REQUIRED = "review_required"
    BLOCKED = "blocked"

class CitationIntent(StrEnum):
    BACKGROUND = "background"
    METHOD = "method"
    RESULT = "result"

class EvidenceRelation(StrEnum):
    DIRECT_SUPPORT = "direct_support"
    INDIRECT_SUPPORT = "indirect_support"
    CONTRADICTS = "contradicts"
    NO_RELATION = "no_relation"

@dataclass(frozen=True, slots=True)
class ClaimView:
    text: str

@dataclass(frozen=True, slots=True)
class SourceSpanView:
    text: str

@dataclass(frozen=True, slots=True)
class TransformationView:
    description: str

@dataclass(frozen=True, slots=True)
class ConfidenceVectorView:
    score: float

@dataclass(frozen=True, slots=True)
class LimitationView:
    reason: str

@dataclass(frozen=True, slots=True)
class AccessDisclosureView:
    level: str

@dataclass(frozen=True, slots=True)
class EvidenceCardView:
    id: UUID
    citation_anchor_id: UUID
    reference_entry_id: UUID
    status: EvidenceLinkStatus
    citation_intents: tuple[CitationIntent, ...]
    evidence_relation: EvidenceRelation
    headline: str
    citing_claim: ClaimView
    source_spans: tuple[SourceSpanView, ...]
    transformations: tuple[TransformationView, ...]
    confidence: ConfidenceVectorView
    limitations: tuple[LimitationView, ...]
    access_disclosure: AccessDisclosureView
