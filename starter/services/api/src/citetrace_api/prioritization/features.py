from typing import Any


def compute_understand_score(features: dict[str, Any]) -> float:
    score = 0.0
    if features.get("foundational"):
        score += 0.4
    if features.get("background"):
        score += 0.2
    return min(1.0, score)

def compute_implement_score(features: dict[str, Any]) -> float:
    score = 0.0
    if features.get("adopted_method"):
        score += 0.5
    if features.get("dataset"):
        score += 0.3
    return min(1.0, score)

def compute_review_score(features: dict[str, Any]) -> float:
    score = 0.0
    if features.get("contradict[str, Any]s"):
        score += 0.6
    if features.get("scope_mismatch"):
        score += 0.4
    return min(1.0, score)

def compute_survey_score(features: dict[str, Any]) -> float:
    score = 0.0
    if features.get("lineage"):
        score += 0.5
    return min(1.0, score)

def compute_present_score(features: dict[str, Any]) -> float:
    score = 0.0
    if features.get("novelty"):
        score += 0.5
    if features.get("key_benchmark"):
        score += 0.5
    return min(1.0, score)
