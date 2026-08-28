from typing import Any
from uuid import UUID

from .models import ExplanationDraft, ExplanationStatement, ExplanationStatementKind


class RelationshipSummaryGenerator:
    def __init__(self, model_gateway: Any = None):
        self.model_gateway = model_gateway

    async def generate_draft(
        self,
        relationship_data: dict[str, Any],
        audience: str = "expert",
        mode: str = "review"
    ) -> ExplanationDraft:
        # Uses prompts/07_relationship_summary.md or prompts/08_beginner_explainer.md
        # Basic mock for tests
        return ExplanationDraft(
            statements=[
                ExplanationStatement(
                    kind=ExplanationStatementKind.EVIDENCE_BASED,
                    text="Mock statement",
                    supporting_citing_span_ids=(UUID("00000000-0000-0000-0000-000000000001"),),
                    supporting_source_span_ids=(UUID("00000000-0000-0000-0000-000000000002"),),
                    confidence=0.9,
                    display_order=1
                )
            ],
            summary_text="Mock summary",
            audience=audience,
            mode=mode
        )
