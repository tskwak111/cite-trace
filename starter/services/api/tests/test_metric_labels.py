"""Tests for metric labels."""

import pytest

from citetrace_api.observability.metrics import InvalidMetricLabelError, increment_counter


def test_allowed_labels() -> None:
    """Test that allowed labels pass validation."""
    increment_counter("analysis_created_total", 1, {"stage": "parsing"})

def test_disallowed_labels() -> None:
    """Test that disallowed labels fail validation."""
    with pytest.raises(InvalidMetricLabelError):
        increment_counter("analysis_created_total", 1, {"user_id": "123"})
