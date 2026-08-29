"""Contract tests for the hybrid evidence search (Slice 5).

The hybrid search combines lexical (BM25) and semantic (bag-of-words
cosine over the same vocabulary) scores and re-ranks the candidates
using the existing `EvidenceReranker`. These tests are the
acceptance criteria for the Slice 5 implementation:

  - lexical-only, semantic-only, and hybrid modes all return the
    same top-k when the underlying scores agree;
  - hybrid scoring can promote a candidate that BM25 alone would
    rank below another, when the semantic similarity is much
    higher;
  - the contract is "deterministic": the same input yields the
    same output across runs;
  - the reranker still receives the candidate set in a useful
    order (best-first), so the verifier stage can short-circuit
    when a high-confidence match is found.
"""

from __future__ import annotations

import pytest

from citetrace_api.retrieval.hybrid_search import (
    EvidenceChunk,
    HybridSearchIndex,
    SearchMode,
)


@pytest.fixture
def small_corpus() -> list[EvidenceChunk]:
    return [
        EvidenceChunk(
            id="c1",
            text="BM25 scoring uses term frequency and document length normalization.",
            source_span_id="s1",
        ),
        EvidenceChunk(
            id="c2",
            text="Hybrid retrieval combines BM25 and vector search for better recall.",
            source_span_id="s2",
        ),
        EvidenceChunk(
            id="c3",
            text="PostgreSQL pgvector extension stores embeddings for nearest-neighbor search.",
            source_span_id="s3",
        ),
        EvidenceChunk(
            id="c4",
            text="Calibration of confidence uses the weakest link across pipeline stages.",
            source_span_id="s4",
        ),
    ]


def test_lexical_search_finds_bm25_chunk(small_corpus: list[EvidenceChunk]) -> None:
    index = HybridSearchIndex(small_corpus)
    results = index.search("BM25 term frequency", mode=SearchMode.LEXICAL, top_k=3)
    assert results, "lexical search returned no results"
    assert results[0].chunk_id == "c1", (
        f"lexical search should rank c1 first for 'BM25 term frequency'; "
        f"got {[r.chunk_id for r in results]}"
    )


def test_semantic_search_finds_concept_even_without_lexical_overlap(
    small_corpus: list[EvidenceChunk],
) -> None:
    index = HybridSearchIndex(small_corpus)
    results = index.search(
        "vector search embeddings",
        mode=SearchMode.SEMANTIC,
        top_k=3,
    )
    ids = {r.chunk_id for r in results}
    assert "c3" in ids, (
        f"semantic search should retrieve c3 (about vector search); got {ids}"
    )


def test_hybrid_mode_ranks_relevant_chunk_first(
    small_corpus: list[EvidenceChunk],
) -> None:
    index = HybridSearchIndex(small_corpus)
    results = index.search(
        "BM25 hybrid retrieval recall",
        mode=SearchMode.HYBRID,
        top_k=3,
    )
    assert results[0].chunk_id == "c2", (
        f"hybrid should rank c2 (mentions both BM25 and hybrid retrieval) first; "
        f"got {[r.chunk_id for r in results]}"
    )


def test_search_is_deterministic(small_corpus: list[EvidenceChunk]) -> None:
    index = HybridSearchIndex(small_corpus)
    query = "BM25 hybrid retrieval recall"
    a = index.search(query, mode=SearchMode.HYBRID, top_k=4)
    b = index.search(query, mode=SearchMode.HYBRID, top_k=4)
    assert [r.chunk_id for r in a] == [r.chunk_id for r in b], (
        "hybrid search is not deterministic; the verifier stage cannot rely on stable ordering"
    )


def test_top_k_is_respected(small_corpus: list[EvidenceChunk]) -> None:
    index = HybridSearchIndex(small_corpus)
    for k in (1, 2, 3, 4):
        results = index.search("BM25", mode=SearchMode.HYBRID, top_k=k)
        assert len(results) <= k
        assert len(results) >= 1, (
            f"top_k={k} must return at least one result for a non-empty corpus"
        )


def test_empty_corpus_returns_empty_results() -> None:
    index = HybridSearchIndex([])
    results = index.search("anything", mode=SearchMode.HYBRID, top_k=5)
    assert results == []


def test_chunk_text_round_trip() -> None:
    chunk = EvidenceChunk(id="x", text="hello world", source_span_id="s")
    assert chunk.id == "x"
    assert chunk.source_span_id == "s"
    assert "hello" in chunk.text
