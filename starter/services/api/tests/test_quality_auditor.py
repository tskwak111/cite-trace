from uuid import uuid4

import pytest

from citetrace_api.audit.service import QualityAuditorService
from citetrace_api.explanations.models import ExplanationStatement, ExplanationStatementKind


@pytest.mark.anyio
async def test_audit_passed():
    service = QualityAuditorService()
    evidence_data = {
        "relation_type": "direct_support",
        "source_spans": ["span1"],
        "statements": [
            ExplanationStatement(
                kind=ExplanationStatementKind.EVIDENCE_BASED,
                text="Test",
                supporting_source_span_ids=(uuid4(),),
                confidence=0.9,
                display_order=1
            )
        ]
    }
    decision = await service.audit(evidence_data)
    assert decision.status == "passed"
    assert not decision.blocking_codes

@pytest.mark.anyio
async def test_audit_blocked_missing_evidence():
    service = QualityAuditorService()
    evidence_data = {
        "relation_type": "direct_support",
        "source_spans": [],
        "statements": []
    }
    decision = await service.audit(evidence_data)
    assert decision.status == "blocked"
    assert "missing_evidence" in decision.blocking_codes
