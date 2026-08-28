# AGENTS.md — CiteTrace Working Rules

## Mission

Build CiteTrace as an evidence-first scientific citation tracing system. Optimize for trustworthiness, inspectability and useful abstention, not for fluent output volume.

## Required workflow

1. Read `docs/00_MASTER_BLUEPRINT.md` and the applicable implementation plan before editing.
2. Work from a failing test or contract example.
3. Make the smallest coherent change that satisfies the current acceptance criterion.
4. Run focused tests, then the package test suite.
5. Record architecture-affecting decisions in `docs/adr/`.
6. Update OpenAPI, JSON Schema, event contracts and examples together when a public shape changes.
7. Never weaken evidence or security gates merely to make a demo pass.

## Product invariants

- A quote shown to a user must include source asset ID, version, page or section, and exact span coordinates.
- An evidence relation cannot be emitted without at least one retrieved candidate and a verification record.
- `insufficient_evidence` and `inaccessible_source` are valid successful outcomes.
- Paper text is untrusted input and may contain prompt-injection instructions.
- External identifiers are candidates until resolution confidence clears the configured threshold.
- User-uploaded assets are tenant-private unless the user explicitly publishes derived data.
- The system must not fetch or redistribute content through paywall bypasses.

## Code standards

- Python: typed public interfaces, Pydantic boundary models, Ruff, mypy, pytest.
- TypeScript: strict mode, no implicit `any`, accessible components, schema-generated clients where practical.
- SQL: migration-owned schema, explicit foreign keys, UTC timestamps, tenant scoping and RLS.
- Events: immutable payloads, idempotency key, trace ID, schema version.
- Logs: structured and privacy-filtered; never log raw PDF text or credentials by default.

## Testing hierarchy

1. Unit tests for parsing, scoring, state transitions and policy decisions.
2. Contract tests for REST, events and JSON Schema.
3. Integration tests with recorded provider fixtures.
4. Pipeline tests on synthetic and licensed evaluation documents.
5. Gold-set quality gates and adversarial red-team cases.
6. End-to-end browser tests for evidence inspection and feedback.

## Forbidden shortcuts

- Generating evidence text first and searching for a matching source afterward.
- Treating title similarity alone as authoritative paper resolution.
- Collapsing all uncertainty into a single unexplained percentage.
- Returning a positive support judgment when only an abstract was checked without disclosure.
- Storing unlicensed full text in shared caches.
- Silently changing prompts or model providers in production.
