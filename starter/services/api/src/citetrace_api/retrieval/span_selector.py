from dataclasses import dataclass
from enum import Enum

from citetrace_api.services.quote_validator import QuoteValidationError, validate_quote


class EvidenceType(Enum):
    text_span = "text_span"
    equation = "equation"
    table_cell_or_region = "table_cell_or_region"
    figure_or_caption = "figure_or_caption"
    algorithm_block = "algorithm_block"
    appendix_span = "appendix_span"
    abstract_span = "abstract_span"


from typing import Any


@dataclass(frozen=True)
class SelectedSourceSpan:
    start_offset: int
    end_offset: int
    page: int | None
    quote: str
    quote_sha256: str
    evidence_type: EvidenceType
    bounding_boxes: tuple[dict[str, Any], ...] = ()
    validation_status: str = "valid"


@dataclass(frozen=True)
class SpanSelectionOutcome:
    spans: list[SelectedSourceSpan]
    status: str
    limitations: list[str]


class ExactSpanSelector:
    def select_span(
        self, normalized_text: str, quote: str, start_offset: int, end_offset: int
    ) -> SpanSelectionOutcome:
        try:
            val = validate_quote(normalized_text, quote, start_offset, end_offset)
            span = SelectedSourceSpan(
                start_offset=val.start_offset,
                end_offset=val.end_offset,
                page=None,
                quote=val.quote,
                quote_sha256=val.quote_sha256,
                evidence_type=EvidenceType.text_span,
            )
            return SpanSelectionOutcome(spans=[span], status="success", limitations=[])
        except QuoteValidationError as e:
            return SpanSelectionOutcome(spans=[], status="failed", limitations=[str(e)])
