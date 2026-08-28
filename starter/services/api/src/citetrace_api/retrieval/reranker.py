from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RerankFeatures:
    lexical_rank: int | None
    vector_rank: int | None
    entity_coverage: float
    qualifier_coverage: float
    negation_compatibility: float
    section_prior: float
    evidence_type_prior: float
    exact_number_match: float


class EvidenceReranker:
    def rank_candidates(self, claim_qualifiers: list[Any], candidates: list[Any]) -> list[Any]:
        return candidates
