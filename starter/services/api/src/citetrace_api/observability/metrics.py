"""Metrics implementation."""

from typing import Any

ALLOWED_LABELS = {
    "stage",
    "status",
    "provider",
    "relation",
    "access_level",
    "reason_code",
}

class InvalidMetricLabelError(Exception):
    """Exception raised when an invalid label is provided."""
    pass

def _validate_labels(labels: dict[str, Any]) -> None:
    """Validate labels against allowed list."""
    for key in labels:
        if key not in ALLOWED_LABELS:
            raise InvalidMetricLabelError(f"Label '{key}' is not allowed. Allowed labels: {ALLOWED_LABELS}")

def increment_counter(name: str, value: int = 1, labels: dict[str, Any] | None = None) -> None:
    """Increment a metric counter."""
    if labels:
        _validate_labels(labels)
    # Dummy implementation for tests

def record_histogram(name: str, value: float, labels: dict[str, Any] | None = None) -> None:
    """Record a histogram value."""
    if labels:
        _validate_labels(labels)
    # Dummy implementation for tests
