from dataclasses import dataclass

from .features import ResolutionFeatures


@dataclass(frozen=True, slots=True)
class ResolutionWeights:
    identifier: float = 0.35
    title: float = 0.25
    authors: float = 0.15
    year: float = 0.08
    venue: float = 0.05
    version: float = 0.07
    provider_agreement: float = 0.05

def weighted_score(features: ResolutionFeatures, weights: ResolutionWeights | None = None) -> float:
    if weights is None:
        weights = ResolutionWeights()

    if features.hard_conflicts:
        return 0.0

    score = (
        features.identifier_score * weights.identifier +
        features.title_score * weights.title +
        features.author_score * weights.authors +
        features.year_score * weights.year +
        features.venue_score * weights.venue +
        features.version_score * weights.version +
        features.provider_agreement_score * weights.provider_agreement
    )

    return max(0.0, min(1.0, score))
