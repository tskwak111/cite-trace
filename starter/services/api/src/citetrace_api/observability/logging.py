"""Logging with safe redaction."""

import logging
import re

# Basic patterns for redaction
REDACTION_PATTERNS = [
    (re.compile(r"Bearer\s+[a-zA-Z0-9\-\._~+/]+=*"), "Bearer [REDACTED]"),
    (re.compile(r"api[_-]?key[_-]?=?[a-zA-Z0-9\-\._~+/]+", re.IGNORECASE), "api_key=[REDACTED]"),
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "sk-[REDACTED]"),
    (re.compile(r"https?://[^/?#]+[^?#]*\?[^#]*X-Goog-Signature=[^&#]+"), "[SIGNED_URL_REDACTED]"),
    (re.compile(r"https?://[^/?#]+[^?#]*\?[^#]*X-Amz-Signature=[^&#]+"), "[SIGNED_URL_REDACTED]"),
]

def redact_sensitive_text(text: str) -> str:
    """Redact sensitive patterns in text."""
    redacted_text = str(text)
    for pattern, replacement in REDACTION_PATTERNS:
        redacted_text = pattern.sub(replacement, redacted_text)
    return redacted_text

class SafeLogFilter(logging.Filter):
    """Filter to redact sensitive data from logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records to redact sensitive information."""
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_text(record.msg)
        if hasattr(record, "args") and record.args:
            if isinstance(record.args, dict):
                redacted_args = {
                    k: redact_sensitive_text(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
                record.args = redacted_args
            elif isinstance(record.args, (list, tuple)):
                redacted_args_list = [
                    redact_sensitive_text(str(v)) if isinstance(v, str) else v
                    for v in record.args
                ]
                record.args = tuple(redacted_args_list)

        return True
