
import pytest

from citetrace_api.explanations.generator import RelationshipSummaryGenerator
from citetrace_api.explanations.models import ExplanationStatementKind


@pytest.mark.anyio
async def test_generate_draft():
    generator = RelationshipSummaryGenerator()
    draft = await generator.generate_draft({}, audience="expert", mode="review")
    
    assert draft.summary_text == "Mock summary"
    assert len(draft.statements) == 1
    assert draft.statements[0].kind == ExplanationStatementKind.EVIDENCE_BASED
    assert len(draft.statements[0].supporting_source_span_ids) > 0
