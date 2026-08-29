import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ConfidenceReason:
    stage: str
    score: float
    reason_code: str


@dataclass(frozen=True)
class ConfidenceVector:
    parse: float
    reference_resolution: float
    source_access: float
    evidence_retrieval: float
    relation_verification: float
    explanation_grounding: float
    weakest_link: float
    balanced_score: float
    calibration_profile: str
    reasons: tuple[ConfidenceReason, ...]


def _geometric_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    clamped = [max(0.0, min(1.0, v)) for v in values]
    if any(v == 0.0 for v in clamped):
        return 0.0
    return math.exp(sum(math.log(v) for v in clamped) / len(clamped))


def calculate_confidence(scores: dict[str, float]) -> ConfidenceVector:
    stage_scores = [scores.get(name, 1.0) for name in (
        "parse",
        "reference_resolution",
        "source_access",
        "evidence_retrieval",
        "relation_verification",
        "explanation_grounding",
    )]
    weakest = min(stage_scores) if stage_scores else 0.0
    balanced = _geometric_mean(stage_scores)
    return ConfidenceVector(
        parse=scores.get("parse", 1.0),
        reference_resolution=scores.get("reference_resolution", 1.0),
        source_access=scores.get("source_access", 1.0),
        evidence_retrieval=scores.get("evidence_retrieval", 1.0),
        relation_verification=scores.get("relation_verification", 1.0),
        explanation_grounding=scores.get("explanation_grounding", 1.0),
        weakest_link=weakest,
        balanced_score=balanced,
        calibration_profile="default",
        reasons=(),
    )
