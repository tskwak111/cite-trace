# ADR-0001: Start with a Modular Monolith and Asynchronous Workers

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

CiteTrace has distinct parsing, resolution, acquisition, retrieval, verification and explanation responsibilities, but the first product is built by a small team and must preserve transactional provenance. Premature microservices would add deployment, schema, observability and failure complexity before independent scaling needs are known.

## Decision

Use one primary application codebase with strict module boundaries and separate asynchronous worker processes. PostgreSQL is the authoritative state store; Redis provides queues and ephemeral coordination. GROBID remains an isolated external service because it processes untrusted documents and has a separate runtime.

## Consequences

- domain and application interfaces must remain independent of FastAPI/provider implementations,
- workers may scale separately by queue,
- modules can be extracted later only with measured scaling/security/deployment need,
- internal module calls are preferred over network calls,
- an ADR is required before adding another runtime service.
