from datetime import UTC, datetime

from citetrace_api.domain.enums import AnalysisStatus
from citetrace_api.domain.models import Analysis, AnalysisProgress


class InvalidTransitionError(ValueError):
    pass


_ALLOWED_TRANSITIONS: dict[AnalysisStatus, frozenset[AnalysisStatus]] = {
    AnalysisStatus.CREATED: frozenset({AnalysisStatus.VALIDATING, AnalysisStatus.CANCELLED}),
    AnalysisStatus.VALIDATING: frozenset(
        {AnalysisStatus.PARSING, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED}
    ),
    AnalysisStatus.PARSING: frozenset(
        {AnalysisStatus.RESOLVING_REFERENCES, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED}
    ),
    AnalysisStatus.RESOLVING_REFERENCES: frozenset(
        {AnalysisStatus.ACQUIRING_SOURCES, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED}
    ),
    AnalysisStatus.ACQUIRING_SOURCES: frozenset(
        {AnalysisStatus.RETRIEVING_EVIDENCE, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED}
    ),
    AnalysisStatus.RETRIEVING_EVIDENCE: frozenset(
        {AnalysisStatus.VERIFYING_RELATIONS, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED}
    ),
    AnalysisStatus.VERIFYING_RELATIONS: frozenset(
        {AnalysisStatus.GENERATING_EXPLANATIONS, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED}
    ),
    AnalysisStatus.GENERATING_EXPLANATIONS: frozenset(
        {AnalysisStatus.AUDITING, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED}
    ),
    AnalysisStatus.AUDITING: frozenset(
        {
            AnalysisStatus.COMPLETED,
            AnalysisStatus.COMPLETED_WITH_LIMITS,
            AnalysisStatus.FAILED,
            AnalysisStatus.CANCELLED,
        }
    ),
    AnalysisStatus.COMPLETED: frozenset(),
    AnalysisStatus.COMPLETED_WITH_LIMITS: frozenset(),
    AnalysisStatus.FAILED: frozenset(),
    AnalysisStatus.CANCELLED: frozenset(),
}

_STAGE_PERCENT: dict[AnalysisStatus, float] = {
    AnalysisStatus.CREATED: 0,
    AnalysisStatus.VALIDATING: 5,
    AnalysisStatus.PARSING: 15,
    AnalysisStatus.RESOLVING_REFERENCES: 30,
    AnalysisStatus.ACQUIRING_SOURCES: 45,
    AnalysisStatus.RETRIEVING_EVIDENCE: 60,
    AnalysisStatus.VERIFYING_RELATIONS: 75,
    AnalysisStatus.GENERATING_EXPLANATIONS: 87,
    AnalysisStatus.AUDITING: 95,
    AnalysisStatus.COMPLETED: 100,
    AnalysisStatus.COMPLETED_WITH_LIMITS: 100,
    AnalysisStatus.FAILED: 100,
    AnalysisStatus.CANCELLED: 100,
}


def transition(analysis: Analysis, target: AnalysisStatus) -> Analysis:
    if target == analysis.status:
        return analysis
    if target not in _ALLOWED_TRANSITIONS[analysis.status]:
        raise InvalidTransitionError(f"cannot transition {analysis.status} -> {target}")

    now = datetime.now(UTC)
    completed_at = now if target.terminal else None
    return analysis.model_copy(
        update={
            "status": target,
            "progress": AnalysisProgress(
                stage=target,
                completed_units=0,
                total_units=0,
                percent=_STAGE_PERCENT[target],
            ),
            "updated_at": now,
            "completed_at": completed_at,
        }
    )
