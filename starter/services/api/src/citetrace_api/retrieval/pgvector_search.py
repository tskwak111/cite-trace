"""pgvector-backed hybrid evidence search.

This module implements the Slice 9 / ADR-0009 adapter that
replaces the in-memory `HybridSearchIndex` with a real
PostgreSQL + pgvector backend. The public surface is the
same as the in-memory index so the call sites do not change.

Fallback policy:

- When `CITETRACE_PGVECTOR_URL` is unset or the connection
  fails, the `build_hybrid_search_index` factory returns the
  in-memory index and logs a single WARNING. The fallback is
  loud, not silent.
- When the URL is set and the connection succeeds, the
  `PgVectorHybridSearchIndex` is used and the embeddings are
  persisted to the `evidence_embedding` table with the
  tenant id supplied at construction time.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from .embeddings import HashedBagOfWordsEmbedding
from .hybrid_search import (
    EvidenceChunk,
    HybridSearchIndex,
    SearchMode,
    SearchResult,
    _tokenize,
)

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 64
PGVECTOR_ENV = "CITETRACE_PGVECTOR_URL"


class PgVectorHybridSearchIndex:
    def __init__(
        self,
        chunks: list[EvidenceChunk],
        *,
        connection_string: str,
        tenant_id: str,
        dim: int = EMBEDDING_DIM,
    ) -> None:
        if not connection_string:
            raise ValueError("connection_string is required")
        if not tenant_id:
            raise ValueError("tenant_id is required")
        self._chunks = list(chunks)
        self._connection_string = connection_string
        self._tenant_id = tenant_id
        self._embedder = HashedBagOfWordsEmbedding(dim=dim)
        self._indexed: set[str] = set()
        self._open_and_init()

    def _open_and_init(self) -> None:
        import psycopg

        with psycopg.connect(self._connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS evidence_embedding (
                        tenant_id text NOT NULL,
                        chunk_id text NOT NULL,
                        source_span_id text NOT NULL,
                        embedding vector({self._embedder.dim}) NOT NULL,
                        text text NOT NULL,
                        tokens jsonb NOT NULL,
                        PRIMARY KEY (tenant_id, chunk_id)
                    )
                    """
                )
            conn.commit()
        self._reindex()

    def _reindex(self) -> None:
        if not self._chunks:
            return
        import psycopg

        rows = []
        for chunk in self._chunks:
            tokens = _tokenize(chunk.text)
            if not tokens:
                continue
            embedding = self._embedder.embed(chunk.text)
            rows.append((self._tenant_id, chunk.id, chunk.source_span_id, embedding, chunk.text, tokens))
        if not rows:
            return
        with psycopg.connect(self._connection_string) as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO evidence_embedding
                        (tenant_id, chunk_id, source_span_id, embedding, text, tokens)
                    VALUES (%s, %s, %s, %s::vector, %s, %s::jsonb)
                    ON CONFLICT (tenant_id, chunk_id) DO UPDATE SET
                        source_span_id = EXCLUDED.source_span_id,
                        embedding = EXCLUDED.embedding,
                        text = EXCLUDED.text,
                        tokens = EXCLUDED.tokens
                    """,
                    [
                        (
                            t,
                            cid,
                            sid,
                            "[" + ",".join(f"{v:.6f}" for v in vec) + "]",
                            txt,
                            _jsonb_tokens(toks),
                        )
                        for (t, cid, sid, vec, txt, toks) in rows
                    ],
                )
            conn.commit()
        self._indexed = {chunk.id for chunk in self._chunks}

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    def search(
        self,
        query: str,
        *,
        mode: SearchMode = SearchMode.HYBRID,
        top_k: int = 5,
    ) -> list[SearchResult]:
        if top_k <= 0 or not self._chunks:
            return []
        tokens = _tokenize(query)
        if not tokens:
            return []
        query_embedding = self._embedder.embed(query)
        query_vec_str = "[" + ",".join(f"{v:.6f}" for v in query_embedding) + "]"

        import psycopg

        with psycopg.connect(self._connection_string) as conn:
            with conn.cursor() as cur:
                if mode is SearchMode.LEXICAL:
                    cur.execute(
                        """
                        SELECT chunk_id, source_span_id,
                               ts_rank_cd(to_tsvector('simple', text), plainto_tsquery('simple', %s)) AS score
                        FROM evidence_embedding
                        WHERE tenant_id = %s
                          AND to_tsvector('simple', text) @@ plainto_tsquery('simple', %s)
                        ORDER BY score DESC
                        LIMIT %s
                        """,
                        (query, self._tenant_id, query, top_k),
                    )
                elif mode is SearchMode.SEMANTIC:
                    cur.execute(
                        """
                        SELECT chunk_id, source_span_id,
                               1 - (embedding <=> %s::vector) AS score
                        FROM evidence_embedding
                        WHERE tenant_id = %s
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                        """,
                        (query_vec_str, self._tenant_id, query_vec_str, top_k),
                    )
                else:
                    cur.execute(
                        """
                        WITH q AS (SELECT plainto_tsquery('simple', %s) AS q, %s::vector AS v)
                        SELECT chunk_id, source_span_id,
                               (
                                   COALESCE(ts_rank_cd(to_tsvector('simple', text), q.q), 0) * 0.5
                                   + (1 - (embedding <=> q.v)) * 0.5
                               ) AS score
                        FROM evidence_embedding, q
                        WHERE tenant_id = %s
                        ORDER BY score DESC
                        LIMIT %s
                        """,
                        (query, query_vec_str, self._tenant_id, top_k),
                    )
                rows = cur.fetchall()
        return [
            SearchResult(chunk_id=cid, source_span_id=sid, score=float(score))
            for cid, sid, score in rows
            if score is not None
        ]


def _jsonb_tokens(tokens: list[str]) -> str:
    import json

    return json.dumps(tokens, ensure_ascii=False)


def build_hybrid_search_index(
    chunks: list[EvidenceChunk],
    *,
    connection_string: str | None = None,
    tenant_id: str | None = None,
) -> Any:
    """Factory that returns the pgvector adapter when the URL is
    reachable, and the in-memory index otherwise. The fallback
    logs a single WARNING so a silent regression cannot hide.
    """
    connection_string = connection_string or os.environ.get(PGVECTOR_ENV)
    if not connection_string:
        logger.warning(
            "CITETRACE_PGVECTOR_URL is not set; falling back to in-memory "
            "HybridSearchIndex. The pgvector adapter is required for "
            "staging and production; see ADR-0009."
        )
        return HybridSearchIndex(chunks)

    try:
        import psycopg
        with psycopg.connect(connection_string, connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
    except Exception as exc:
        logger.warning(
            "pgvector at %s is not reachable (%s); falling back to "
            "in-memory HybridSearchIndex. The pgvector adapter is required "
            "for staging and production; see ADR-0009.",
            connection_string,
            exc.__class__.__name__,
        )
        return HybridSearchIndex(chunks)

    if not tenant_id:
        raise ValueError(
            "tenant_id is required when CITETRACE_PGVECTOR_URL is set; "
            "the pgvector adapter enforces tenant isolation at the table level"
        )
    return PgVectorHybridSearchIndex(
        chunks,
        connection_string=connection_string,
        tenant_id=tenant_id,
    )
