"""Tracing helpers."""

import contextlib
from collections.abc import Iterator


@contextlib.contextmanager
def trace_context(name: str) -> Iterator[None]:
    """Basic dummy helper for trace context."""
    # In a real implementation this would use OpenTelemetry
    yield
