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


def calculate_confidence(scores: dict[str, float]) -> ConfidenceVector:
    weakest = min(scores.values()) if scores else 0.0
    balanced = sum(scores.values()) / len(scores) if scores else 0.0
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
