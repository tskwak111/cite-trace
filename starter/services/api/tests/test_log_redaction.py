"""Tests for log redaction."""

import logging

from citetrace_api.observability.logging import SafeLogFilter, redact_sensitive_text


def test_redact_sensitive_text() -> None:
    """Test redacting text directly."""
    assert redact_sensitive_text("My token is Bearer 12345-abc!") == "My token is Bearer [REDACTED]!"
    assert redact_sensitive_text("Key sk-123456789012345678901234") == "Key sk-[REDACTED]"
    assert redact_sensitive_text("api_key=mysecretkey") == "api_key=[REDACTED]"

def test_safe_log_filter() -> None:
    """Test log filter."""
    log_filter = SafeLogFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Using Bearer secret-token-abc",
        args=(),
        exc_info=None
    )
    log_filter.filter(record)
    assert record.msg == "Using Bearer [REDACTED]"
