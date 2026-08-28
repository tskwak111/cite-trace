from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class TransformationKind(Enum):
    adopted_unchanged = "adopted_unchanged"
    parameter_changed = "parameter_changed"
    domain_transferred = "domain_transferred"
    extended = "extended"
    simplified = "simplified"
    combined = "combined"
    benchmark_only = "benchmark_only"
    dataset_reused = "dataset_reused"
    metric_reused = "metric_reused"
    conceptual_inspiration = "conceptual_inspiration"


@dataclass(frozen=True)
class TransformationRecord:
    kind: TransformationKind
    description: str
    supporting_citing_span_id: UUID | None
    supporting_source_span_id: UUID | None
    changed_dimensions: dict[str, str]


class TransformationAnalyzer:
    pass
