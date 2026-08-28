from hashlib import sha256

import pytest

from citetrace_api.services.quote_validator import QuoteValidationError, validate_quote


def test_exact_quote_and_offsets_are_accepted() -> None:
    text = "Evidence must be inspectable."
    result = validate_quote(text, "must be inspectable", 9, 28)

    assert result.quote_sha256 == sha256(b"must be inspectable").hexdigest()


def test_mismatched_quote_is_rejected() -> None:
    with pytest.raises(QuoteValidationError, match="quote_does_not_match_asset"):
        validate_quote("Evidence must be inspectable.", "must be plausible", 9, 26)


def test_out_of_bounds_offsets_are_rejected() -> None:
    with pytest.raises(QuoteValidationError, match="offset_out_of_bounds"):
        validate_quote("short", "short", 0, 10)
