"""Cross-module integration contract for retrieval → verification →
calibration → explanation (Slice 6).

The contract is intentionally narrow: it asserts that the four
modules can be composed through their existing public APIs and
that the result is consistent with the blueprint invariants
(docs/00_MASTER_BLUEPRINT.md §13, §14, §15).

If a future slice replaces one of these modules with a live
implementation, the integration test must continue to pass with
the real implementation behind the same interface.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from citetrace_api.calibration.confidence import calculate_confidence
from citetrace_api.calibration.profiles import determine_publish_status
from citetrace_api.explanations.generator import RelationshipSummaryGenerator
from citetrace_api.retrieval.hybrid_search import (
    EvidenceChunk,
    HybridSearchIndex,
    SearchMode,
)
from citetrace_api.verification.relations import EvidenceRelation
from citetrace_api.verification.service import RelationVerificationService


@dataclass
class IntegrationCase:
    name: str
    access_level: str
    corpus: list[EvidenceChunk]
    query: str
    expected_relation: EvidenceRelation
    expected_status: str


CASES = [
    IntegrationCase(
        name="direct_support_path",
        access_level="open_access_full_text",
        corpus=[
            EvidenceChunk(
                id="a",
                text="BM25 scoring uses term frequency and document length normalization.",
                source_span_id="sa",
            ),
            EvidenceChunk(
                id="b",
                text="The calibration paper shows geometric mean of stage scores.",
                source_span_id="sb",
            ),
        ],
        query="BM25 term frequency scoring",
        expected_relation=EvidenceRelation.direct_support,
        expected_status="verified",
    ),
    IntegrationCase(
        name="inaccessible_source_path",
        access_level="not_accessible",
        corpus=[],
        query="anything",
        expected_relation=EvidenceRelation.inaccessible_source,
        expected_status="blocked",
    ),
    IntegrationCase(
        name="no_relevant_evidence_path",
        access_level="open_access_full_text",
        corpus=[
            EvidenceChunk(
                id="x",
                text="This corpus is about an unrelated topic in cell biology.",
                source_span_id="sx",
            ),
        ],
        query="BM25 retrieval ranking algorithm",
        expected_relation=EvidenceRelation.no_relevant_evidence,
        expected_status="blocked",
    ),
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_end_to_end_pipeline_contract(case: IntegrationCase) -> None:
    index = HybridSearchIndex(case.corpus)
    retrieved = index.search(case.query, mode=SearchMode.HYBRID, top_k=5)

    verifier = RelationVerificationService()
    decision = verifier.verify(case.access_level, retrieved)

    assert decision.relation == case.expected_relation, (
        f"{case.name}: expected {case.expected_relation}, got {decision.relation}"
    )

    if case.expected_relation is EvidenceRelation.inaccessible_source:
        stage_scores = {
            "parse": 0.9,
            "reference_resolution": 0.9,
            "source_access": 0.2,
            "evidence_retrieval": 0.0,
            "relation_verification": 1.0,
            "explanation_grounding": 0.0,
        }
    elif case.expected_relation is EvidenceRelation.no_relevant_evidence:
        stage_scores = {
            "parse": 0.9,
            "reference_resolution": 0.9,
            "source_access": 0.9,
            "evidence_retrieval": 0.0,
            "relation_verification": 1.0,
            "explanation_grounding": 0.5,
        }
    else:
        stage_scores = {
            "parse": 0.9,
            "reference_resolution": 0.9,
            "source_access": 0.9,
            "evidence_retrieval": 0.9,
            "relation_verification": 0.9,
            "explanation_grounding": 0.9,
        }

    vector = calculate_confidence(stage_scores)
    status = determine_publish_status(vector.weakest_link, vector.balanced_score)

    assert status == case.expected_status, (
        f"{case.name}: expected publish status {case.expected_status}, "
        f"got {status} (weakest_link={vector.weakest_link}, "
        f"balanced={vector.balanced_score})"
    )

    generator = RelationshipSummaryGenerator()
    draft = asyncio.run(
        generator.generate_draft(
            {
                "relation": decision.relation.value,
                "confidence": vector.balanced_score,
                "weakest_link": vector.weakest_link,
            }
        )
    )
    assert draft.summary_text, f"{case.name}: explanation draft summary is empty"
    assert draft.summary_text, (
        f"{case.name}: explanation draft must contain a non-empty summary; got {draft.summary_text!r}"
    )


def test_geometric_mean_propagates_through_pipeline() -> None:
    """A weak retrieval stage must keep the analysis from being
    'verified' even when retrieval finds nothing; the geometric
    mean must reflect that."""
    index = HybridSearchIndex([])
    retrieved = index.search("BM25", mode=SearchMode.HYBRID, top_k=5)
    verifier = RelationVerificationService()
    decision = verifier.verify("open_access_full_text", retrieved)
    assert decision.relation is EvidenceRelation.no_relevant_evidence

    vector = calculate_confidence({
        "parse": 0.95,
        "reference_resolution": 0.95,
        "source_access": 0.95,
        "evidence_retrieval": 0.0,
        "relation_verification": 1.0,
        "explanation_grounding": 0.95,
    })
    assert vector.weakest_link == 0.0
    status = determine_publish_status(vector.weakest_link, vector.balanced_score)
    assert status == "blocked", (
        f"weakest link 0.0 must produce 'blocked'; got {status}"
    )
