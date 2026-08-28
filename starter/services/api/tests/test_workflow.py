from uuid import uuid4

import pytest

from citetrace_api.domain.enums import AnalysisMode, AnalysisStatus, Audience
from citetrace_api.domain.models import Analysis, AnalysisCreateRequest, WholeDocumentScope
from citetrace_api.services.workflow import InvalidTransitionError, transition


def _analysis() -> Analysis:
    return Analysis.create(
        AnalysisCreateRequest(
            workspace_id=uuid4(),
            document_id=uuid4(),
            mode=AnalysisMode.UNDERSTAND,
            scope=WholeDocumentScope(),
            audience=Audience.BEGINNER,
            source_policy_profile="lawful-open-or-user-upload",
        )
    )


def test_valid_transition_updates_status_and_progress() -> None:
    updated = transition(_analysis(), AnalysisStatus.VALIDATING)

    assert updated.status == AnalysisStatus.VALIDATING
    assert updated.progress.percent == 5
    assert updated.completed_at is None


def test_invalid_transition_is_rejected() -> None:
    with pytest.raises(InvalidTransitionError, match="cannot transition"):
        transition(_analysis(), AnalysisStatus.RETRIEVING_EVIDENCE)


def test_terminal_transition_sets_completed_at() -> None:
    validating = transition(_analysis(), AnalysisStatus.VALIDATING)
    cancelled = transition(validating, AnalysisStatus.CANCELLED)

    assert cancelled.status.terminal
    assert cancelled.completed_at is not None
