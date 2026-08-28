from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from citetrace_api.providers.models import ProviderCandidate

from .features import ResolutionFeatures


@dataclass(frozen=True, slots=True)
class ResolutionDecision:
    status: str
    selected_candidate_id: str | None
    selected_work_version_id: UUID | None
    absolute_score: float | None
    score_margin: float | None
    reason_codes: tuple[str, ...]
    requires_human_review: bool


def decide_resolution(
    scored_candidates: Sequence[tuple[ProviderCandidate, float, ResolutionFeatures]],
    threshold_accept: float = 0.90,
    threshold_margin: float = 0.08,
    threshold_ambiguous_floor: float = 0.80,
) -> ResolutionDecision:
    if not scored_candidates:
        return ResolutionDecision(
            status="unresolved",
            selected_candidate_id=None,
            selected_work_version_id=None,
            absolute_score=None,
            score_margin=None,
            reason_codes=("no_candidates",),
            requires_human_review=False,
        )

    sorted_cands = sorted(scored_candidates, key=lambda x: x[1], reverse=True)
    top_cand, top_score, _ = sorted_cands[0]

    margin = top_score
    if len(sorted_cands) > 1:
        margin = top_score - sorted_cands[1][1]

    cand_id = f"{top_cand.provider}:{top_cand.provider_record_id}"

    if top_score >= threshold_accept and margin >= threshold_margin:
        return ResolutionDecision(
            status="resolved",
            selected_candidate_id=cand_id,
            selected_work_version_id=None,
            absolute_score=top_score,
            score_margin=margin,
            reason_codes=(),
            requires_human_review=False,
        )
    elif top_score >= threshold_ambiguous_floor:
        return ResolutionDecision(
            status="ambiguous",
            selected_candidate_id=None,
            selected_work_version_id=None,
            absolute_score=top_score,
            score_margin=margin,
            reason_codes=("ambiguous_candidates",)
            if len(sorted_cands) > 1 and margin < threshold_margin
            else ("needs_review",),
            requires_human_review=True,
        )
    else:
        return ResolutionDecision(
            status="unresolved",
            selected_candidate_id=None,
            selected_work_version_id=None,
            absolute_score=top_score,
            score_margin=margin,
            reason_codes=("low_score",),
            requires_human_review=False,
        )
