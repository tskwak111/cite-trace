from dataclasses import dataclass
from typing import Any


@dataclass
class ExtractedClaim:
    text: str
    qualifiers: list[dict[str, Any]]
    citation_intents: list[str]


@dataclass(frozen=True)
class EvidenceQueryPlan:
    lexical_queries: tuple[str, ...]
    semantic_queries: tuple[str, ...]
    contrast_queries: tuple[str, ...]
    entity_constraints: dict[str, str]
    section_hints: tuple[str, ...]


class EvidenceQueryPlanner:
    def plan_queries(self, claim: ExtractedClaim) -> EvidenceQueryPlan:
        # Dummy deterministic rule fallback
        return EvidenceQueryPlan(
            lexical_queries=(claim.text,),
            semantic_queries=(),
            contrast_queries=(),
            entity_constraints={},
            section_hints=(),
        )
