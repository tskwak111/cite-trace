from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True, slots=True)
class ValidatedQuote:
    quote: str
    start_offset: int
    end_offset: int
    quote_sha256: str


class QuoteValidationError(ValueError):
    pass


def validate_quote(
    normalized_text: str,
    quote: str,
    start_offset: int,
    end_offset: int,
) -> ValidatedQuote:
    if start_offset < 0 or end_offset <= start_offset:
        raise QuoteValidationError("invalid_offset_range")
    if end_offset > len(normalized_text):
        raise QuoteValidationError("offset_out_of_bounds")
    if normalized_text[start_offset:end_offset] != quote:
        raise QuoteValidationError("quote_does_not_match_asset")
    return ValidatedQuote(
        quote=quote,
        start_offset=start_offset,
        end_offset=end_offset,
        quote_sha256=sha256(quote.encode("utf-8")).hexdigest(),
    )
