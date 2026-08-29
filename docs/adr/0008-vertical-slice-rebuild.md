# ADR-0008: Full Rebuild as a Sequence of Vertical Slices

- **Status:** Accepted
- **Date:** 2026-08-29

## Context

The CiteTrace package currently contains a complete and validated design layer
(`docs/`, `contracts/`, `prompts/`, `eval/`) plus a runnable foundation in
`starter/services/api/` (122 pytest passing, 3 known provider-DOI failures,
17/17 contract validators green). Several residual items lower the production
trust posture that the product is meant to embody:

- the root `src/` tree is a stub skeleton that is not imported anywhere and is
  not covered by CI, creating a false impression of a second implementation;
- root-level one-shot generators (`generate_code.py`, `generate_batch2.sh`,
  `fix_ts.js`) and `starter/services/api/generate_task3*.py` /
  `generate_task4.py` remain tracked even though their output is already in
  the tree, and `generate_code.py` references a `tests/` directory that was
  removed in commit `05d7a6d`;
- `scripts/run_release_evaluation.py` hard-codes `"passed": True` and the
  `release_gate` test asserts on that hard-coded value, which is incompatible
  with the AGENTS.md rule "never weaken evidence or security gates merely to
  make a demo pass";
- `starter/ops/runbooks/*.md` are 11–36-byte placeholders, and
  `starter/ops/deploy/base/*.yaml` are 4-line Kubernetes stubs;
- the GROBID client is mocked in tests, the hybrid retrieval path is
  represented by `HybridEvidenceIndex` stubs in `src/`, and the production
  infrastructure artifacts are templates only;
- the human-annotated gold set required for credible release gating
  (300–500 cases) is missing — only 4 synthetic sample cases exist;
- the baseline test run has 3 pre-existing failures
  (`test_crossref_provider`, `test_openalex_provider`,
  `test_semantic_scholar_provider` — all about DOI-before-title lookup) that
  must be classified and either fixed or explicitly de-scoped.

A user request was received to raise the package to "AAA quality". In
CiteTrace terms (per AGENTS.md), AAA means: every published quote is
inspectable to a source version and span, every evidence relation has a
verification record, abstention and inaccessible sources are first-class
outcomes, and every release claim is reproducible from tests and gold-set
metrics. Rebuilding the product in one large change would violate the
"smallest coherent change" rule, would lose the rollback points needed to
preserve evidence gates, and would exceed any single response budget.

## Decision

Rebuild CiteTrace as a **sequence of vertical slices**, each delivered as one
conventional commit per ADR section, in this order. Each slice is a
self-contained merge of code, tests, contracts and documentation, with a
failing test written before the implementation.

1. **Slice 1 — Dead-asset cleanup.** Remove `src/`, root generators,
   `fix_ts.js`, `starter/services/api/generate_task*.py`. Strengthen
   `.gitignore` for `__pycache__` and `.venv`. Collapse the duplicated
   migration into the canonical `contracts/db/schema.sql`. The release
   script and `release_gate` test are *not* touched yet (Slice 2).
2. **Slice 2 — Honest release evaluation.** Rewrite
   `scripts/run_release_evaluation.py` to delegate to
   `scripts/score_sample_predictions.py`, fail with exit code 2 on empty
   gold set, and update `test_release_gate.py` to assert on the new
   contract. Add `eval/goldset_required_columns` check.
3. **Slice 3 — Operational runbooks.** Replace 11–36-byte runbook
   placeholders and 4-line K8s stubs with procedures that can actually be
   executed. Add `ops/runbooks/CONTRIBUTING.md` so future slices add
   real content not stubs.
4. **Slice 4 — GROBID live integration.** Add a docker-compose smoke test
   that brings up GROBID 0.9.1, calls the real `GrobidClient` against a
   fixture PDF, and asserts on `tei_reader` output. Keep the existing
   in-memory fixtures as the default for unit tests.
5. **Slice 5 — Hybrid retrieval.** Implement BM25 + pgvector hybrid
   scoring in `starter/services/api/src/citetrace_api/retrieval/`, with
   pgvector integration behind a connection-pool boundary and a
   feature-flag (`config/feature-flags.example.yaml`).
6. **Slice 6 — Verifier / Transformation / Calibrator integration.**
   Add cross-module integration tests that exercise the full
   retrieval → verification → calibration → explanation chain on a
   frozen fixture, asserting on the published EvidenceCard contract.
7. **Slice 7 — Gold-set pipeline.** Add a CSV-driven ingestion tool,
   a synthetic-seed generator, and CI enforcement that fails the build
   when the gold set has fewer than the configured minimum.
8. **Slice 8 — Production infrastructure.** Provide Terraform / Helm
   inputs, an OpenTelemetry collector config, a secret-manager boundary
   documented in `SECURITY.md`, and a runbook-driven restore drill.

Slices 4–8 require external infrastructure (Docker for GROBID, PostgreSQL
18 with pgvector 0.8.6, live provider API keys, cloud account). When the
environment cannot supply them, the slice is delivered as a *contract test
plus a docker-compose smoke target* — never as a silently-passing stub.

## Consequences

- Every slice produces a separate ADR section, a separate commit, and a
  reproducible `pytest` run; a failed slice can be reverted without
  touching the others.
- The product invariants in AGENTS.md remain enforced at every slice
  boundary; no slice may weaken a gate to pass a test.
- Slice 2 changes the behaviour of the release gate, so it must land
  before any slice that introduces a real gold set.
- The user-visible rebuild is bounded by what the running environment can
  exercise; a slice that requires Docker/PostgreSQL/API keys will be
  marked as "contract-only" if those are absent, never as "passed".
- The root `pyproject.toml` will be reduced to a workspace marker once
  `src/` is removed; downstream installs continue to use
  `starter/services/api/pyproject.toml`.
- The three pre-existing provider-DOI failures are addressed as part of
  Slice 4, because they require live provider fixtures.

## Out of scope (explicitly)

- Rewriting `docs/00_MASTER_BLUEPRINT.md`. The blueprint is the
  source of truth; rebuilds must conform to it, not the reverse.
- Replacing Pydantic v1 models in `src/claims/models.py` (those files
  are removed in Slice 1).
- Changing the prompt versions in `prompts/`. Prompt changes require
  their own ADR per the contributing rules.
- Multi-tenant auth, billing, and a public SaaS deployment. These
  remain in the "first credible release" checklist and are not part of
  this rebuild.
