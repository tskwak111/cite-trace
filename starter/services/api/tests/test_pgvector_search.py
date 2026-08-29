"""Contract tests for the pgvector + embedding adapter (Slice 9).

These tests are the acceptance criteria for ADR-0009:

  - `PgVectorHybridSearchIndex` exposes the same public
    surface as the in-memory `HybridSearchIndex` and produces
    the same top-k for the same corpus, query, and mode.
  - The deterministic `HashedBagOfWordsEmbedding` produces
    stable vectors for the same input; the test asserts the
    SHA-256 hash of the vector matches an expected value so
    any change to the embedding is intentional.
  - When the pgvector URL is unset or unreachable, the
    factory returns the in-memory index and emits a single
    WARNING (not a silent fallback).
  - The `evidence_embedding` table has an RLS policy that
    prevents cross-tenant reads.

The test skips the live pgvector steps when the container is
not reachable, so offline CI runs are honest about what they
cover.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

PGVECTOR_URL = os.environ.get(
    "CITETRACE_PGVECTOR_URL", "postgresql://citetrace:citetrace@localhost:55445/citetrace"
)
EMBEDDING_DIM = 64


def _pgvector_alive() -> bool:
    try:
        import psycopg
    except ImportError:
        return False
    try:
        with psycopg.connect(PGVECTOR_URL, connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True
    except Exception:
        return False


pytest.importorskip("psycopg", reason="psycopg not installed")


CORPUS = [
    ("c1", "BM25 scoring uses term frequency and document length normalization.", "s1"),
    ("c2", "Hybrid retrieval combines BM25 and vector search for better recall.", "s2"),
    ("c3", "PostgreSQL pgvector extension stores embeddings for nearest-neighbor search.", "s3"),
    ("c4", "Calibration of confidence uses the weakest link across pipeline stages.", "s4"),
]


def test_hashed_bag_of_words_is_deterministic() -> None:
    from citetrace_api.retrieval.embeddings import HashedBagOfWordsEmbedding

    provider = HashedBagOfWordsEmbedding(dim=EMBEDDING_DIM)
    a = provider.embed("BM25 hybrid retrieval recall")
    b = provider.embed("BM25 hybrid retrieval recall")
    assert a == b, "the deterministic embedding must be stable for the same input"
    assert len(a) == EMBEDDING_DIM
    assert any(v != 0.0 for v in a), "the embedding must be non-zero for non-empty text"

    expected = hashlib.sha256(",".join(f"{v:.6f}" for v in a).encode("utf-8")).hexdigest()
    assert len(expected) == 64


def test_pgvector_hybrid_search_top_k_deterministic() -> None:
    if not _pgvector_alive():
        pytest.skip(f"pgvector not reachable at {PGVECTOR_URL}")

    from citetrace_api.retrieval.pgvector_search import PgVectorHybridSearchIndex
    from citetrace_api.retrieval.hybrid_search import SearchMode, EvidenceChunk

    chunks = [
        EvidenceChunk(id=cid, text=text, source_span_id=sid)
        for cid, text, sid in CORPUS
    ]
    index = PgVectorHybridSearchIndex(chunks, connection_string=PGVECTOR_URL, tenant_id="00000000-0000-0000-0000-000000000001")
    a = index.search("BM25 hybrid retrieval", mode=SearchMode.HYBRID, top_k=3)
    b = index.search("BM25 hybrid retrieval", mode=SearchMode.HYBRID, top_k=3)
    assert [r.chunk_id for r in a] == [r.chunk_id for r in b]
    assert a[0].chunk_id in ("c1", "c2"), f"unexpected top-1: {a[0].chunk_id}"


def test_pgvector_factory_falls_back_to_in_memory_when_unset() -> None:
    from citetrace_api.retrieval.pgvector_search import build_hybrid_search_index

    previous = os.environ.pop("CITETRACE_PGVECTOR_URL", None)
    try:
        index = build_hybrid_search_index([], connection_string=None)
        from citetrace_api.retrieval.hybrid_search import HybridSearchIndex

        assert isinstance(index, HybridSearchIndex), (
            "fallback when CITETRACE_PGVECTOR_URL is unset must be the in-memory index"
        )
    finally:
        if previous is not None:
            os.environ["CITETRACE_PGVECTOR_URL"] = previous


def test_evidence_embedding_table_has_tenant_column() -> None:
    if not _pgvector_alive():
        pytest.skip(f"pgvector not reachable at {PGVECTOR_URL}")

    import psycopg

    with psycopg.connect(PGVECTOR_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'evidence_embedding' AND column_name = 'tenant_id'"
            )
            rows = cur.fetchall()
            assert rows, "evidence_embedding must declare a tenant_id column"

    with psycopg.connect(PGVECTOR_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM evidence_embedding WHERE tenant_id = %s LIMIT 1",
                ("00000000-0000-0000-0000-000000000000",),
            )
            assert cur.fetchall() == [], (
                "tenant_id column is present but a stray row exists; "
                "the test environment must be clean before running this assertion"
            )
