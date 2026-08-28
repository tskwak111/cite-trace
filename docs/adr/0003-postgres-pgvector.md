# ADR-0003: PostgreSQL with pgvector as the Primary Data Platform

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

CiteTrace needs relational integrity for provenance and tenant policy, plus vector retrieval over source chunks. Introducing separate operational databases early would complicate consistency and deletion.

## Decision

Use PostgreSQL for authoritative relational data and pgvector for initial embedding search. Object bytes reside in S3-compatible storage; Redis is non-authoritative.

## Consequences

- evidence/provenance transactions can be enforced with foreign keys,
- row-level security supports tenant isolation,
- hybrid lexical/vector retrieval can start in one platform,
- embedding dimensions and profiles are versioned; incompatible vectors are not mixed,
- a separate search/vector service requires measured scale and an ADR.
