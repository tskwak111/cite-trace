# ADR-0009: pgvector + embedding adapter for hybrid search

- **Status:** Accepted
- **Date:** 2026-08-29

## Context

Slice 5 added a pure-Python `HybridSearchIndex` to satisfy the
unit-test contract for hybrid BM25 + cosine retrieval. The
interface is small (`EvidenceChunk`, `SearchResult`, `SearchMode`,
`search()`) precisely so a real backend can replace the
in-memory index without changing the call sites. The master
blueprint §15 calls for pgvector-backed nearest-neighbour
search against real embeddings; v1.1.0 explicitly listed the
pgvector adapter as a non-goal of the slice because it
required a live PostgreSQL instance.

This ADR is the deliberate landing of that adapter. The
deployment environment now has `pgvector/pgvector:pg18` running
locally (port 55445), the canonical schema is applied
(including RLS), and the API's existing dev dependencies
already include `psycopg[binary,pool]`.

## Decision

Add a `PgVectorHybridSearchIndex` that:

1. Uses the same public surface as the in-memory index
   (`search(query, mode=..., top_k=...)` returning
   `list[SearchResult]`).
2. Persists `chunks` to a small `evidence_embedding` table
   (one row per chunk) with the embedding as a `vector`
   column. The table has a `tenant_id` column and an RLS
   policy that mirrors the rest of the schema, so a chunk
   cannot leak across tenants.
3. Uses **deterministic, no-network embeddings** for the
   contract: a SHA-256-seeded hashed-bag-of-words
   pseudo-embedding. The provider API is *not* called in the
   contract test; a real embedding provider is a follow-up
   ADR. This keeps the test offline-stable and CI-fast.
4. Falls back to the in-memory index automatically when
   `CITETRACE_PGVECTOR_URL` is unset or the connection fails.
   The fallback is logged once at WARNING level so a silent
   regression cannot hide.

A new abstraction `EmbeddingProvider` is added with two
implementations:

- `HashedBagOfWordsEmbedding` — the deterministic offline
  provider, 64-dimensional.
- `PassthroughEmbedding` — accepts pre-computed vectors,
  used by the contract test to control scores.

The schema does not change; the `evidence_embedding` table is
declared in this ADR as an additive migration and is applied
by `scripts/build_goldset.py migrate-pgvector` (or the
existing migration runner). The canonical
`contracts/db/schema.sql` is updated in the same commit.

## Consequences

- The hybrid search has a real backend option for staging
  and production; the unit tests stay offline-stable.
- The fallback to the in-memory index is loud (one WARNING),
  not silent. The release pipeline can detect the fallback by
  grepping the worker log for the marker.
- The deterministic embedding means the same corpus produces
  the same top-k across runs; the contract test
  `test_pgvector_hybrid_search_top_k_deterministic` asserts
  this against a real container.
- A future ADR will add a real embedding provider (OpenAI
  text-embedding-3-small, etc.) behind the same
  `EmbeddingProvider` interface. Switching providers will
  not change the call sites.

## Out of scope (explicitly)

- A real embedding provider (any network call to an LLM
  provider). The deterministic hashed-bag-of-words is the
  contract; the provider is a follow-up.
- HNSW vs IVFFLAT index choice. The current implementation
  uses exact nearest-neighbour (`<=>` operator without an
  index) which is correct for the small contract corpus. The
  production index strategy is a follow-up that needs a
  larger gold set to tune.
- Cross-encoder reranking. The existing `EvidenceReranker`
  remains the cross-encoder slot; this ADR does not change it.
- Replacing the in-memory index everywhere. The in-memory
  index remains the default for unit tests and for environments
  without a pgvector URL; the pgvector adapter is opt-in.
