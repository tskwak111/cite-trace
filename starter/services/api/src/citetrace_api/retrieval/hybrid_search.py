"""Hybrid lexical + semantic evidence search.

This module implements the Slice 5 hybrid retrieval that the
master blueprint describes. It is intentionally dependency-free
(pure Python, no numpy / scikit-learn / pgvector client) so that
the unit tests and the offline contract checks run without any
external infrastructure. The interface is shaped so a future
pgvector-backed implementation can replace `HybridSearchIndex`
without changing the call sites.

Design:

- `EvidenceChunk` is a single retrieved candidate (the same
  concept the rest of the pipeline uses).
- `HybridSearchIndex` builds, on construction, an in-memory
  inverted index for BM25 (lexical) and a term-vector
  representation for cosine similarity (semantic).
- `search(query, mode, top_k)` returns a list of
  `SearchResult` ordered by the selected scoring strategy.

The BM25 parameters (k1=1.5, b=0.75) match the Okapi defaults
that work well on scientific abstracts in our evaluation. They
are exposed as constructor parameters so a future tuning run
can override them.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from enum import Enum


class SearchMode(str, Enum):
    LEXICAL = "lexical"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text)]


@dataclass(frozen=True)
class EvidenceChunk:
    id: str
    text: str
    source_span_id: str


@dataclass(frozen=True)
class SearchResult:
    chunk_id: str
    score: float
    source_span_id: str


class HybridSearchIndex:
    def __init__(
        self,
        chunks: list[EvidenceChunk],
        *,
        bm25_k1: float = 1.5,
        bm25_b: float = 0.75,
        semantic_weight: float = 0.5,
    ) -> None:
        if not 0.0 <= semantic_weight <= 1.0:
            raise ValueError("semantic_weight must be in [0, 1]")
        self._chunks = list(chunks)
        self._bm25_k1 = bm25_k1
        self._bm25_b = bm25_b
        self._semantic_weight = semantic_weight

        self._tokenized: list[list[str]] = [_tokenize(c.text) for c in self._chunks]
        self._doc_freq: Counter[str] = Counter()
        self._doc_len: list[int] = [len(toks) for toks in self._tokenized]
        for toks in self._tokenized:
            for term in set(toks):
                self._doc_freq[term] += 1
        self._avg_doc_len = (
            sum(self._doc_len) / len(self._doc_len) if self._doc_len else 0.0
        )
        self._term_freq: list[Counter[str]] = [Counter(toks) for toks in self._tokenized]
        self._vocab: set[str] = set()
        for toks in self._tokenized:
            self._vocab.update(toks)
        self._idf: dict[str, float] = {
            term: math.log(
                1 + (len(self._chunks) - df + 0.5) / (df + 0.5)
            )
            for term, df in self._doc_freq.items()
        }
        self._doc_vectors: list[dict[str, float]] = [self._vectorise(tf) for tf in self._term_freq]

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    def _vectorise(self, term_freq: Counter[str]) -> dict[str, float]:
        if not term_freq:
            return {}
        norm = math.sqrt(sum(1.0 for _ in term_freq))
        return {term: 1.0 / norm for term in term_freq}

    def _bm25_scores(self, query_tokens: list[str]) -> list[float]:
        if not self._chunks:
            return []
        scores = [0.0] * len(self._chunks)
        for term in query_tokens:
            idf = self._idf.get(term, 0.0)
            if idf == 0.0:
                continue
            for idx, tf in enumerate(self._term_freq):
                freq = tf.get(term, 0)
                if freq == 0:
                    continue
                dl = self._doc_len[idx]
                denom = freq + self._bm25_k1 * (
                    1 - self._bm25_b + self._bm25_b * dl / max(self._avg_doc_len, 1e-9)
                )
                scores[idx] += idf * (freq * (self._bm25_k1 + 1)) / denom
        return scores

    def _semantic_scores(self, query_tokens: list[str]) -> list[float]:
        if not self._chunks or not query_tokens:
            return [0.0] * len(self._chunks)
        query_vec = self._vectorise(Counter(query_tokens))
        if not query_vec:
            return [0.0] * len(self._chunks)
        scores: list[float] = []
        for doc_vec in self._doc_vectors:
            score = 0.0
            for term, weight in query_vec.items():
                score += weight * doc_vec.get(term, 0.0)
            scores.append(score)
        return scores

    def search(
        self,
        query: str,
        *,
        mode: SearchMode = SearchMode.HYBRID,
        top_k: int = 5,
    ) -> list[SearchResult]:
        if top_k <= 0:
            return []
        if not self._chunks:
            return []
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        if mode is SearchMode.LEXICAL:
            scores = self._bm25_scores(query_tokens)
        elif mode is SearchMode.SEMANTIC:
            scores = self._semantic_scores(query_tokens)
        else:
            lex = self._bm25_scores(query_tokens)
            sem = self._semantic_scores(query_tokens)
            lex_max = max(lex) or 1.0
            sem_max = max(sem) or 1.0
            w = self._semantic_weight
            scores = [
                (1 - w) * (l / lex_max) + w * (s / sem_max)
                for l, s in zip(lex, sem)
            ]

        ranked = sorted(
            enumerate(scores),
            key=lambda pair: (-pair[1], pair[0]),
        )
        results: list[SearchResult] = []
        for idx, score in ranked[:top_k]:
            if score <= 0:
                continue
            chunk = self._chunks[idx]
            results.append(
                SearchResult(
                    chunk_id=chunk.id,
                    score=score,
                    source_span_id=chunk.source_span_id,
                )
            )
        return results
