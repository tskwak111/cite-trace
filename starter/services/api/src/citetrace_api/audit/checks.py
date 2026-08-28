from typing import Any


def check_quote_exact_match(source_text: str, quote: str) -> bool:
    return quote in source_text

def check_offset_valid(source_text: str, offset_start: int, offset_end: int) -> bool:
    return not (offset_start < 0 or offset_end > len(source_text) or offset_start > offset_end)

def check_relation_has_evidence(relation_type: str, source_spans: list[Any]) -> bool:
    if relation_type in ("abstain", "insufficient_evidence", "inaccessible_source"):
        return True
    return len(source_spans) >= 1

def check_statement_grounding(statement_kind: str, source_span_ids: list[Any]) -> bool:
    if statement_kind == "evidence_based":
        return len(source_span_ids) >= 1
    return True

def check_access_disclosure(claimed_access: str, source_asset_access: str) -> bool:
    return claimed_access == source_asset_access

def check_schema_valid(payload: dict[str, Any], schema: dict[str, Any]) -> bool:
    # simple mock
    return True

def check_prompt_injection_resistance(quote: str) -> bool:
    forbidden = ["ignore previous", "system prompt", "instruction"]
    return not any(f in quote.lower() for f in forbidden)

def check_auditor_independence(route: str) -> bool:
    return route != "main_generation_route"
