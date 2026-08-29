# Changelog

All notable package changes are documented here. Dates use ISO 8601.

## [1.5.0] - 2026-08-29

### Fixed

- **Slice 12 — Next.js full build + Playwright 3-pane verification.**
  The web app shipped with `strict: true` but five components
  declared untyped props (TS7031) and the feedback test used
  `jest.fn()` under vitest (TS2708). The build itself failed
  on `@tailwind` directives because Tailwind was not
  configured.

  This commit:
    - types `NoteComposer`, `ExportDialog`, and
      `EvidenceFeedbackDialog` props with explicit
      `*Props` interfaces and re-exports the payload types
      (`NoteDraft`, `ExportFormat`, `FeedbackCategory`,
      `FeedbackPayload`).
    - converts the `feedback-dialog.test.tsx` mock from
      `jest.fn()` to `vi.fn()` so the vitest run is green.
    - adds `tailwind.config.js`, `postcss.config.js`, and
      the `tailwindcss / postcss / autoprefixer` dev
      dependencies, so the production build (`pnpm build`)
      no longer fails on the `@tailwind` directive.
    - adds `tests/three-pane-reader.spec.ts` (5 Playwright
      tests) that boots `next start --port 3001` and asserts
      the three-pane shell renders with reference map,
      paper, and evidence panes in the expected order, and
      that the page returns a non-5xx response.
    - extends the `web` CI job with `pnpm test`,
      Playwright browser install, and the 3-pane e2e run.

### Notes

- 189 API tests pass; 10 vitest unit tests pass; 5
  Playwright e2e tests pass; the production `pnpm build`
  produces 3 static pages from the App Router.
- The e2e suite uses `next start` against a static
  prerendered build; the future interactive reader flows
  (upload, citation click, evidence card) are covered by
  the existing placeholder specs and will be expanded as
  the reader becomes interactive.

## [1.4.0] - 2026-08-29

### Added

- **Slice 11 — GROBID robustness fixtures and tests.** A new
  `scripts/build_grobid_robustness_fixtures.py` generates six
  deterministic PDFs that cover the production failure modes:
  multi-page, truncated xref, garbage payload, zero-byte, CJK,
  and Greek characters. A new
  `tests/test_grobid_robustness.py` runs ten contract tests
  against the `GrobidClient`:
    - multi-page TEI contains two pages
    - truncated PDF surfaces 4xx/5xx
    - garbage PDF surfaces 4xx
    - empty PDF surfaces 4xx
    - CJK codepoints round-trip through the response reader
    - Greek codepoints round-trip
    - 5xx with eventual 200 succeeds after retry
    - live multi-page PDF reports both `<surface>` elements
    - live truncated PDF raises `GrobidClientError`
    - all robustness fixtures are present on disk

  The `respx` mocks cover the offline contract; the two live
  tests run in the `grobid-smoke` CI job against a real
  `grobid/grobid:0.9.1-crf` container.

### Notes

- 189 API tests pass; 9 GROBID smoke tests are explicitly
  skipped when the container is not reachable.

## [1.3.0] - 2026-08-29

### Added

- **Slice 10 — live blocking-metric collection (ADR-0010).**
  `scripts/collect_live_blocking_metrics.py` measures the three
  blocking metrics the release gate could not synthesise:
    - `schema_valid_rate` — fraction of evidence-link payloads
      that pass the evidence-link.v1 schema's required-key
      contract;
    - `cross_tenant_access_failures` — count of audit decisions
      that recorded a cross-tenant access attempt;
    - `inaccessible_source_false_full_text_claims` — count of
      evidence links whose source was `not_accessible` but whose
      confidence vector records full-text grounding.
  The script is single-tenant by construction; `--tenant-id` is
  required and the script `SET LOCAL app.tenant_id` before any
  read. A missing or unreachable tenant context is a hard
  failure; a missing measurement is reported as `null`, never
  zero. Exit codes: 0 (within thresholds), 1 (blocking metric
  violated), 2 (empty window).
- `run_release_evaluation.py --live-metrics` accepts a JSON
  file produced by the collector and applies the rubric to the
  live values, no longer treating them as unmeasured. The
  acceptance path for a release is now:
    1. `collect_live_blocking_metrics.py` against a staging
       database (Slice 10 output);
    2. `run_release_evaluation.py --live-metrics ...` against
       the human-annotated gold set (Slice 7 gate).
- `tests/test_live_blocking_metrics.py` (4 contract tests:
  empty window → exit 2, real run → exit 0, missing tenant →
  hard failure, missing metric ≠ 0).
- `tests/test_release_evaluation_script.py` gains a
  `test_synthetic_with_live_metrics_passes` that asserts the
  end-to-end release gate passes when the synthetic samples
  are scored against a clean live-metric report.
- CI: a new step in the `pgvector-smoke` job runs the live
  collector smoke test against the same PostgreSQL container.

### Notes

- 181 API tests pass; 7 GROBID live-smoke tests are explicitly
  skipped when the container is not reachable.
- The release pipeline now has a real path to a green gate
  on a small staging run, even before the 300-case human gold
  set exists. The 300-case minimum remains a separate gate
  enforced by `scripts/build_goldset.py preflight`.

## [1.2.0] - 2026-08-29

### Added

- **Slice 9 — pgvector + embedding adapter.** A new
  `citetrace_api.retrieval.pgvector_search` module implements
  `PgVectorHybridSearchIndex` with the same public surface as
  the in-memory `HybridSearchIndex`. The adapter persists
  embeddings to a new `evidence_embedding` table backed by
  `pgvector` (64-dim) and uses PostgreSQL's `ts_rank_cd` for
  the lexical leg and the `<=>` cosine distance for the
  semantic leg, combined at `0.5 / 0.5` in the hybrid leg.
  A new `citetrace_api.retrieval.embeddings` module exposes
  a deterministic `HashedBagOfWordsEmbedding` (offline,
  no-network) and a `PassthroughEmbedding` for tests. The
  factory `build_hybrid_search_index` falls back to the
  in-memory index when `CITETRACE_PGVECTOR_URL` is unset or
  unreachable and logs a single WARNING; the fallback is
  loud, never silent.
- **ADR-0009** documents the design, the fallback policy,
  and the explicit out-of-scope list (real embedding
  provider, HNSW vs IVFFLAT, cross-encoder reranking).
- **`tests/test_pgvector_search.py`** with four contract
  tests (deterministic embedding, deterministic top-k,
  factory fallback, tenant column presence).
- **CI** adds a `pgvector-smoke` job that brings up a real
  `pgvector/pgvector:pg18` container, applies the canonical
  schema, and runs the smoke test.
- **Issue and PR templates** (`.github/ISSUE_TEMPLATE/`,
  `.github/PULL_REQUEST_TEMPLATE.md`) so that new
  contributors and AI agents are forced to confront the
  AGENTS.md invariants before opening a PR or filing an
  issue.

### Notes

- 176 API tests pass; 7 GROBID live-smoke tests are
  explicitly skipped when the container is not reachable.
- The pgvector adapter is opt-in. The in-memory index
  remains the default for unit tests and for environments
  without a pgvector URL.

## [1.1.0] - 2026-08-29

### Changed

- **Slice 1 — dead assets removed.** The root `src/` Python stub
  tree, the root-level one-shot generators (`generate_code.py`,
  `generate_batch2.sh`, `fix_ts.js`) and the
  `starter/services/api/generate_task*.py` files are deleted.
  The root `pyproject.toml` is now a workspace marker only; the
  shipped Python package continues to live in
  `starter/services/api/`. The `contracts/db/schema.sql` and
  `starter/services/api/migrations/0001_initial.sql` are
  byte-locked together and the lock is enforced by a contract
  test (`tests/test_schema_sync.py`).
- **Slice 2 — honest release evaluation.** The 34-line
  hard-coded `"passed": True` stub in
  `scripts/run_release_evaluation.py` is replaced with a real
  evaluator that delegates to `score_sample_predictions.py`,
  fails with exit code 2 on an empty gold set, fails with exit
  code 1 when a blocking metric is violated, and refuses to
  pass when a blocking metric is unmeasured (which is the
  correct behaviour for the synthetic contract). The release
  gate therefore cannot be silently bypassed on synthetic
  samples alone.
- **Slice 3 — operational runbooks are real procedures.** The
  11–36-byte placeholders in `starter/ops/runbooks/` and the
  4-line Kubernetes stub manifests in
  `starter/ops/deploy/base/` are replaced with substantive
  procedures. A contract test in `starter/ops/tests/` enforces
  the minimum length and the required fields of each artifact.
- **Slice 4 — GROBID live integration.** A live integration
  smoke test (`tests/test_grobid_live_smoke.py`) runs against a
  real `grobid/grobid:0.9.1-crf` container in CI; the test is
  explicitly skipped when the container is not reachable, so
  offline runs are honest about what they cover. The three
  pre-existing provider-DOI test failures
  (`crossref_uses_exact_doi_before_title_search`,
  `openalex_uses_exact_doi_before_title_search`,
  `semantic_scholar_uses_exact_doi_before_title_search`) are
  fixed by switching their fixture paths to
  `Path(__file__).parent / "fixtures" / "provider" / ...`.
- **Slice 5 — hybrid evidence search.** A pure-Python
  `HybridSearchIndex` (BM25 + bag-of-words cosine) is added at
  `citetrace_api/retrieval/hybrid_search.py`. The interface is
  small enough that a future pgvector-backed implementation can
  replace the in-memory index without changing the call sites.
- **Slice 6 — verifier / calibration / explanation integration.**
  The `ConfidenceVector.balanced_score` is now the geometric
  mean of stage scores, matching the master blueprint §13. The
  arithmetic mean could mask a 0.0 stage behind several 1.0
  stages; the geometric mean does not. A four-case integration
  test (`tests/test_pipeline_integration.py`) exercises the
  retrieval → verification → calibration → explanation path
  end-to-end on the three expected outcomes (direct support,
  inaccessible source, no relevant evidence).
- **Slice 7 — gold-set pipeline.** `scripts/build_goldset.py`
  provides CSV↔JSONL conversion, a preflight check that
  refuses to release below the 300-case / 8-domain minimum
  (or requires an explicit `--override` recorded in the
  release audit log), and a synthetic-seed generator that
  exercises all 9 evidence relations across 12 research
  domains.
- **Slice 8 — production infrastructure.** The OpenTelemetry
  collector config (`ops/observability/otel-collector.yaml`),
  the Helm chart (`ops/release/helm/`), the Terraform
  variables (`ops/deploy/terraform.tfvars`), and the
  secret-manager boundary (`ops/secrets/secret_manager_boundary.yaml`)
  are added. The secret boundary declares the rotation policy
  for every secret in the deployment and the three
  application-level boundaries (no on-disk persistence, no
  observability export, no user-facing embedding).

### Added

- ADR-0008: vertical-slice rebuild plan.
- `VERIFICATION_REPORT_2026-08-29.md` reporting the v1.1 state.
- 31 new contract tests across 6 new test files.

### Notes

- 172 API tests + 20 ops tests + 8 contract validators pass.
- 7 GROBID live-smoke tests are explicitly skipped when the
  container is not reachable.
- The release gate refuses to pass on synthetic samples
  alone; the 300-case human gold set is the next blocker for
  a "first credible release" build, and is tracked outside
  this rebuild.

## [1.0.0] - 2026-08-28

### Added

- master product blueprint, PRD, competitive strategy, taxonomy, system and AI architecture,
- provenance, API/event, UX, evaluation, security, SRE, roadmap, risk, GTM and operating specifications,
- seven architecture decision records,
- OpenAPI 3.1, event catalog, PostgreSQL/pgvector schema, RLS policies and JSON Schemas,
- machine-readable citation-intent, evidence-relation, transformation and feedback taxonomies,
- schema-bound agent prompt pack with independent quality auditor,
- synthetic evaluation set, scoring script, annotation handbook and gold-set template,
- four TDD implementation plans organized as independently testable vertical slices,
- FastAPI foundation with idempotent analyses, transition guards, SSE and exact-quote validation,
- Next.js three-pane evidence-reader shell,
- Docker Compose dependencies and CI workflow,
- executable contract examples and cross-contract drift validation,
- repository governance, security policy, contribution rules and verification report.

### Known maturity boundary

The package is implementation-ready but is not a deployed production service. Provider credentials, production authentication, secure object storage, parser integration, source acquisition, evidence retrieval/verifier execution, human gold-set annotation, and production infrastructure remain implementation work governed by the included plans.
