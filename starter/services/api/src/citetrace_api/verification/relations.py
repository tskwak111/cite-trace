from dataclasses import dataclass
from enum import Enum
from typing import Any


class EvidenceRelation(Enum):
    direct_support = "direct_support"
    partial_support = "partial_support"
    indirect_support = "indirect_support"
    contradicts = "contradicts"
    overgeneralized = "overgeneralized"
    scope_mismatch = "scope_mismatch"
    no_relevant_evidence = "no_relevant_evidence"
    insufficient_evidence = "insufficient_evidence"
    inaccessible_source = "inaccessible_source"


@dataclass(frozen=True)
class RelationDecision:
    relation: EvidenceRelation
    confidence: float
    scope_observations: list[dict[str, Any]]
    reason_codes: tuple[str, ...]
    review_required: bool
    abstention_reason: str | None = None
