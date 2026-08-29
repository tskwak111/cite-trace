# Changelog

All notable package changes are documented here. Dates use ISO 8601.

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
