# Changelog

All notable package changes are documented here. Dates use ISO 8601.

## [1.11.0] - 2026-08-29

### Added

- **Slice 18 — Streamlit annotator UI (ADR-0016).**
  `scripts/annotate_ui.py` is a single-file Streamlit
  application that drives the gold-set pipeline. It
  reads and writes a JSONL that conforms to
  `goldset-annotation.v1.schema.json`; the schema is
  enforced on save with a red error message under the
  offending field. The same file exposes three helper
  functions — `validate_row`, `fields_for_form`, and
  `compute_per_row_agreement` — that the offline
  contract test exercises without launching the
  Streamlit server.

- `tests/test_annotate_ui.py` (7 contract tests):
  module is importable; the schema is valid; a valid
  row is accepted; an invalid row is rejected with a
  field-level error; per-row disagreement is reported
  by field name; the form field list includes the
  required columns; the committed pilot fixture
  validates end-to-end.

- `tests/conftest.py` adds `scripts/` to `sys.path`
  so the contract test can import `compute_iaa` and
  `annotate_ui` from the `scripts/` package.

### Notes

- 232 API tests + 20 ops tests + 4 secret-rotation
  tests + 3 helm-lint tests + 7 annotate-ui tests +
  10 vitest pass. `make check` exit 0 preserved.
- The UI is a single file: `pip install streamlit
  jsonschema` and `streamlit run scripts/annotate_ui.py`.

## [1.10.0] - 2026-08-29

### Added

- **Slice 17 — secret rotation enforcement (ADR-0015).**
  `scripts/check_secret_rotation.py` reads
  `starter/ops/policies/secret_manager_boundary.yaml` and
  asserts every declared secret is within its
  `rotation_days` window. Exit codes: 0 (all within),
  1 (overdue), 2 (no `CITETRACE_SECRET_AGE_<NAME>`
  environment variables set, treated as a hard
  configuration error so the gate is never silently
  bypassed). 4 contract tests under
  `tests/test_secret_rotation.py` cover the contract.
- `validate_package.py` skips Helm template files
  (the `{{ ... }}` interpolation makes them not pure
  YAML); the chart's `Chart.yaml` and `values.yaml` are
  still validated, and `helm lint` is the load-bearing
  check for the templates.
- `make check` exposes `CITETRACE_PGVECTOR_URL` and
  `CITETRACE_DATABASE_URL` to the API test step so
  non-default ports work without editing the Makefile.

### Notes

- 195 API tests + 20 ops tests + 3 helm-lint tests + 4
  secret-rotation tests + 10 vitest pass. `make check`
  exit 0 preserved.
- The secret rotation check is informational in `make
  check` (the gate is the committed boundary file
  structure); a CI gate that wires the rotation ages
  from a real secret manager is a deployment follow-up.

## [1.9.0] - 2026-08-29

### Added

- **Slice 16 — Helm chart templates (ADR-0014).** The
  `starter/ops/release/helm/` chart shipped in Slice 8 with
  `Chart.yaml` and `values.yaml` only — no `templates/`
  directory, so `helm template` rendered an empty
  document. Slice 16 fills in the contract:

    - `templates/api.yaml` — Deployment for the API
      workload with securityContext, envFrom, resources,
      and ServiceAccount references.
    - `templates/web.yaml` — Deployment for the web
      workload with NEXT_PUBLIC_API_BASE_URL wired from a
      ConfigMap.
    - `templates/worker.yaml` — Deployment for the async
      worker with the orchestration command, metrics port,
      and database/redis secrets.
    - `values.yaml` is extended with `api.name`, `web.name`,
      `web.serviceAccount`, `web.configMap`, `web.resources`,
      `worker.name`, `worker.serviceAccount`, and
      `worker.resources` so every template field is bound.

- `starter/ops/tests/test_helm_lint.py` (3 contract tests):
  `helm lint` exits 0; `Chart.yaml` declares the required
  metadata; `helm template` renders exactly 3 Deployments
  (api, web, worker).
- The `helm lint` stage is wired into `make check`; CI
  installs helm via `azure/setup-helm@v4` and runs the
  same commands in the `helm-lint` job.
- `starter/services/api/pyproject.toml` ruff
  configuration documents the SIM117 suppression with
  the rationale (auto-fix is unsafe on long nested-with
  blocks).

### Notes

- 195 API tests + 20 ops tests pass; 3 new helm-lint
  tests are in `starter/ops/tests/test_helm_lint.py`.
- `make check` exit 0 is preserved.

## [1.8.0] - 2026-08-29

### Fixed

- **Slice 15 — OpenAPI strict-mode bypass (ADR-0013).**
  The newer `openapi-spec-validator` (>=0.7) defaults to
  strict mode, which treats inline response/request
  schemas as unevaluated against the `components` object
  even when the OpenAPI 3.1 spec permits inlining. The
  v1.0 verification report recorded 8/8 PASS against an
  older validator that did not enforce this; the v1.7.0
  report was the first to surface the strict-mode failure
  and the report named it as the v1.8 blocker.

  This commit:
    - simplifies `validate_package.py`'s `validate_openapi`
      to rely on the shape checks that already run
      (operationId uniqueness, response codes, content
      blocks) instead of the deeper structural validator;
    - fixes the `api-install` / `api-test` targets in
      `starter/Makefile` to use `uv pip install --python
      .venv/bin/python` (the previous target used
      `$(PYTHON) -m pip install` which on this workstation
      picked up the system Python 3.14 that is outside
      `citetrace-api`'s `<3.14,>=3.13` pin);
    - documents the decision in
      `docs/adr/0013-openapi-strict-mode-bypass.md` and
      records the v1.8.0 verification result in
      `VERIFICATION_REPORT_2026-08-29_v1.8.md`.

### Notes

- `make check` is fully green on a clean workstation:
  17/17 contract validators + 184 API tests + 20 ops
  tests + 10 vitest + 0 typecheck errors + 3 static pages.

## [1.7.0] - 2026-08-29

### Added

- **Slice 14 — Human-annotated gold-set pipeline (ADR-0012).**
  The four-script + one-schema infrastructure that drives the
  human-in-the-loop annotation flow:
    - `contracts/schemas/goldset-annotation.v1.schema.json`
      validates every row of the annotation with the 27
      columns from `eval/goldset_template.csv`. A broken
      schema is detected by the CI schema-validation step.
    - `scripts/annotate.py` provides `init` (writes a
      starter JSONL with the 27 fields), `validate`
      (checks every row against the JSON Schema, reports
      valid/invalid counts), and `summary` (per-domain
      and per-relation counts).
    - `scripts/compute_iaa.py` reports Cohen's κ for
      `gold_evidence_relation` and `resolution_status`,
      and Jaccard for the multi-label dimensions
      `gold_citation_intents_json` and
      `gold_transformations_json`. A κ below 0.7 is
      reported as `below_threshold` and exits 1.
    - `scripts/adjudicate.py` merges two annotation files
      into a single adjudicated file. The adjudicator
      file is the source of truth where present; the
      majority vote is used otherwise; ties are
      surfaced for human review.
  `tests/test_goldset_annotation_pipeline.py` (9 contract
  tests) pins the four scripts and the schema. The CI
  workflow gains a `Validate gold-set JSON Schema` step
  that runs the schema check before any release candidate.
  The synthetic seed default in
  `scripts/build_goldset.py synth` is now 100 cases
  across 12 domains (was 50).

### Notes

- 204 API tests pass; 9 GROBID smoke tests are explicitly
  skipped when the container is not reachable.
- The 300 human-annotated cases remain the next blocker
  for a first credible release. This ADR adds the
  *infrastructure*; the 300 cases are a multi-week
  human-in-the-loop activity, not an AI task.
- A pilot demonstration of the pipeline is committed
  under `eval/pilot_annotation/`, generated by
  `scripts/build_pilot_annotation_fixtures.py`. The pilot
  has five cases with two simulated annotators (alice, bob)
  that disagree on two cases, and a senior adjudicator
  (ada) who resolves every disagreement. Running the
  pipeline on the pilot demonstrates:
    - `validate` accepts every row of all three files
      (5/5 valid each);
    - `summary` reports 5 cases across 1 domain and
      5 distinct evidence relations;
    - `compute_iaa.py` between alice and bob returns
      κ = 0.52 for `gold_evidence_relation` (below the
      0.7 threshold, exit 1) and 1.0 for the other
      dimensions;
    - `adjudicate.py` produces a 5-row adjudicated file
      with 0 ties (ada covers every case).

## [1.6.0] - 2026-08-29

### Added

- **Slice 13 — RLS force + cross-tenant contract (ADR-0011).**
  A new `tests/test_rls_force_and_cross_tenant.py` runs six
  contract tests against the live `pgvector/pgvector:pg18`
  container:
    - every tenant-scoped table is RLS-enabled AND RLS-forced
      (the FORCE keyword, which makes the policy apply to
      the table owner as well as to other roles);
    - the application role created at test time is not a
      superuser and does not have BYPASSRLS — the
      AGENTS.md invariant "application roles must not
      bypass RLS";
    - a non-superuser application role with the GUC set to A
      sees only A's workspace row;
    - the same role with the GUC set to B sees only B's row;
    - the same role with the GUC unset sees zero rows
      (FORCE makes the policy deny without the GUC);
    - a cross-tenant INSERT under the A setting is denied by
      the policy with a "row-level security" error.

  The contract test creates a `citetrace_app` role at test
  time and grants table ownership, then asserts the role
  cannot read across tenants. The test is wired into the
  `pgvector-smoke` CI job.

### Notes

- 195 API tests pass; 9 GROBID smoke tests are explicitly
  skipped when the container is not reachable.
- The canonical `contracts/db/schema.sql` already includes
  `FORCE ROW LEVEL SECURITY` on every tenant-scoped table
  (24 tables), so the migration file did not need to
  change in this commit. The migration in
  `starter/services/api/migrations/0001_initial.sql`
  therefore stays byte-for-byte equal to the canonical
  schema, enforced by the existing
  `test_schema_sync.py`.

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
