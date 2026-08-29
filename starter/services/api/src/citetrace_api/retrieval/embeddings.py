"""Embedding providers for the hybrid evidence search.

Two providers are exposed:

- `HashedBagOfWordsEmbedding` is a deterministic, offline
  provider that hashes tokens into a fixed-dimension vector.
  It produces the same vector for the same input every run
  and is used as the contract for the pgvector adapter; a
  real provider (OpenAI text-embedding-3-small, etc.) is a
  follow-up ADR behind the same `EmbeddingProvider` interface.

- `PassthroughEmbedding` accepts pre-computed vectors, used
  by tests to control similarity scores.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


class EmbeddingProvider(Protocol):
    @property
    def dim(self) -> int: ...

    def embed(self, text: str) -> list[float]: ...


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


class HashedBagOfWordsEmbedding:
    """Deterministic, offline, no-network embedding.

    Each token is hashed into one of `dim` buckets and its
    contribution is the natural log of its term frequency.
    The vector is L2-normalised so the dot product is a
    cosine similarity.
    """

    def __init__(self, dim: int = 64) -> None:
        if dim <= 0:
            raise ValueError("dim must be positive")
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self._dim
        if not text:
            return vector
        counts: dict[int, int] = {}
        for token in _tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self._dim
            counts[bucket] = counts.get(bucket, 0) + 1
        for bucket, count in counts.items():
            vector[bucket] = 1.0 + math.log(count)
        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            return vector
        return [v / norm for v in vector]


class PassthroughEmbedding:
    """Embedding provider that returns the supplied vector verbatim.

    The vector is length-checked once and stored. Used by tests
    that need to control the similarity scores.
    """

    def __init__(self, vector: list[float]) -> None:
        if not vector:
            raise ValueError("vector must be non-empty")
        self._vector = list(vector)
        self._dim = len(vector)

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, text: str) -> list[float]:
        return list(self._vector)
