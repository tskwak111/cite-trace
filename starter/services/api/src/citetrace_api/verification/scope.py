from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ScopeComparison:
    compatibility: str
    reason_code: str
    mismatched_dimensions: tuple[str, ...]
    citing_values: dict[str, Any]
    source_values: dict[str, Any]


def compare_scope(citing: dict[str, Any], source: dict[str, Any]) -> ScopeComparison:
    return ScopeComparison("compatible", "exact_match", (), citing, source)
