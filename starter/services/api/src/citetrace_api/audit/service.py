from typing import Any

from pydantic import BaseModel

from . import checks


class AuditDecision(BaseModel):
    status: str
    check_results: list[dict[str, Any]]
    blocking_codes: list[str]

class QualityAuditorService:
    def __init__(self, model_gateway: Any = None):
        self.model_gateway = model_gateway

    async def audit(self, evidence_data: dict[str, Any]) -> AuditDecision:
        results = []
        blocking_codes = []

        # Example check application based on specs
        # Normally would run all the deterministic checks against the evidence_data structure

        # Check relation has evidence
        has_evidence = checks.check_relation_has_evidence(
            evidence_data.get("relation_type", "direct_support"),
            evidence_data.get("source_spans", [])
        )
        results.append({"check": "relation_has_evidence", "passed": has_evidence})
        if not has_evidence:
            blocking_codes.append("missing_evidence")

        if evidence_data.get("statements"):
            for s in evidence_data["statements"]:
                grounded = checks.check_statement_grounding(s.kind, s.supporting_source_span_ids)
                results.append({"check": "statement_grounding", "passed": grounded})
                if not grounded:
                    blocking_codes.append("ungrounded_statement")
                    break

        status = "blocked" if blocking_codes else "passed"

        return AuditDecision(
            status=status,
            check_results=results,
            blocking_codes=blocking_codes
        )
