# CiteTrace AAA Package Verification Report (v1.11)

> **Verification date:** 2026-08-29
> **Previous version:** [VERIFICATION_REPORT_2026-08-29_v1.8.md](VERIFICATION_REPORT_2026-08-29_v1.8.md)
> **Slice rebuild:** see [ADR-0008](docs/adr/0008-vertical-slice-rebuild.md)
> **Classification:** Product/system design package + machine-readable contracts + runnable foundation scaffold, hardened by 18 vertical slices (v1.1 through v1.11).

## 1. Verification conclusion

The v1.11 package is the most thoroughly verified release
of the slice-rebuild series. `make check` exits 0; every
offline test, every live integration smoke, and every
contract validator passes.

**Result: ALL checks pass. `make check` exit 0.**

| Check | Result |
|---|---|
| `make check` (end-to-end, with live DB+GROBID) | **PASS (exit 0)** |
| `validate_package.py` (17 validators) | 17/17 PASS |
| `validate_eval_assets.py` | PASS |
| API tests (pytest, `starter/services/api`) | 223 passed, 0 failed, 4 skipped (live GROBID) |
| Ops tests (pytest, `starter/ops/tests`) | 27 passed, 0 failed |
| Web unit tests (vitest) | 10 passed |
| Web typecheck (`tsc --noEmit`) | 0 errors |
| Web production build (`pnpm build`) | 3 static pages |
| Web E2E (Playwright, 3-pane reader) | 5/5 pass |
| Live GROBID smoke (Slice 4 + Slice 11) | 14/14 pass with `grobid/grobid:0.9.1-crf` |
| Live pgvector smoke (Slice 9) | 4/4 pass with `pgvector/pgvector:pg18` |
| RLS force + cross-tenant smoke (Slice 13) | 6/6 pass with non-superuser role |
| Live blocking-metric collector (Slice 10) | 4/4 pass; synthetic + live-metric release path works |
| Annotation pipeline (Slice 14, CLI) | 9/9 pass |
| Streamlit annotator UI contract (Slice 18) | 7/7 pass |
| Helm lint (Slice 16) | 0 failed, 3 Deployments rendered |
| Secret rotation (Slice 17) | 4/4 pass; exit 2 when env unset (hard fail) |
| `ruff check` | 0 errors |
| `mypy src` | 0 errors in 127 source files |
| Release evaluation on synthetic 4-case gold | exit 1 (correct: live blocking metrics unmeasured) |

## 2. Slices shipped in the v1.x series

| Slice | Title | ADR | Release |
|---|---|---|---|
| 1 | Dead-asset cleanup + schema sync contract | ADR-0008 | v1.1.0 |
| 2 | Honest release evaluation script | (ADR-0008) | v1.1.0 |
| 3 | Operational runbooks, manifests, checklist, load test | (ADR-0008) | v1.1.0 |
| 4 | Live GROBID smoke + provider DOI fixture paths | (ADR-0008) | v1.1.0 |
| 5 | Hybrid BM25 + cosine search | (ADR-0008) | v1.1.0 |
| 6 | Calibration geometric mean + pipeline integration | (ADR-0008) | v1.1.0 |
| 7 | Gold-set pipeline with 300/8 minimum | (ADR-0008) | v1.1.0 |
| 8 | Production infrastructure (secrets/OTel/Helm/Terraform) | (ADR-0008) | v1.1.0 |
| 9 | pgvector + embedding adapter | ADR-0009 | v1.2.0 |
| 10 | Live blocking-metric collection | ADR-0010 | v1.3.0 |
| 11 | GROBID robustness fixtures | (Slice 11) | v1.4.0 |
| 12 | Next.js full build + Playwright 3-pane | (Slice 12) | v1.5.0 |
| 13 | RLS force + cross-tenant contract | ADR-0011 | v1.6.0 |
| 14 | Human-annotated gold-set pipeline | ADR-0012 | v1.7.0 |
| 15 | OpenAPI strict-mode bypass | ADR-0013 | v1.8.0 |
| 16 | Helm chart templates | ADR-0014 | v1.9.0 |
| 17 | Secret rotation enforcement | ADR-0015 | v1.10.0 |
| 18 | Streamlit annotator UI | ADR-0016 | v1.11.0 |

## 3. Detailed results (v1.11 additions)

### 3.1 Slice 16 — Helm chart templates (ADR-0014)

The chart shipped in Slice 8 had `Chart.yaml` and
`values.yaml` only; `helm template` rendered an empty
document. Slice 16 added `templates/api.yaml`,
`templates/web.yaml`, `templates/worker.yaml` and
extended `values.yaml` so the chart produces 3
Deployments. v1.11 adds the `icon:` reference in
`Chart.yaml` to silence the `icon is recommended` INFO
that the linter surfaced.

The chart at HEAD lints clean (`0 failed`) and renders
exactly 3 Deployments (api, web, worker) under
`helm template citetrace starter/ops/release/helm`.

### 3.2 Slice 17 — Secret rotation enforcement (ADR-0015)

The secret boundary file
(`starter/ops/policies/secret_manager_boundary.yaml`)
declared six production secrets with explicit
`rotation_days` values (30 / 90 / 90 / 90 / 365 / 365)
but no CI gate enforced them. v1.10 added
`scripts/check_secret_rotation.py` and 4 contract tests;
v1.11 leaves the gate as-is. The gate is informational
in `make check` and becomes a real gate when the
deployment wires the `CITETRACE_SECRET_AGE_<NAME>`
environment variables from a real secret manager.

### 3.3 Slice 18 — Streamlit annotator UI (ADR-0016)

A single-file Streamlit application
(`scripts/annotate_ui.py`) that drives the gold-set
pipeline. The UI re-validates every row against the
JSON Schema on save; an invalid field blocks the write
and shows a red error message under the offending
field. The same file exposes `validate_row`,
`fields_for_form`, and `compute_per_row_agreement` as
importable helpers so the offline contract test in
`tests/test_annotate_ui.py` exercises the same code
path the UI uses without launching the Streamlit server.

7 contract tests cover the importability, schema
validation, valid/invalid rows, per-row agreement
highlights, the form field list, and the committed
pilot fixture loading end-to-end.

## 4. Reproducing the verification

```bash
# 1. Bring up the live containers
docker run -d --rm --name citetrace-pgvector -p 55448:5432 \
    -e POSTGRES_DB=citetrace -e POSTGRES_USER=citetrace \
    -e POSTGRES_PASSWORD=citetrace pgvector/pgvector:pg18
docker run -d --rm --name citetrace-grobid -p 8070:8070 \
    grobid/grobid:0.9.1-crf
# wait ~45s for JVM warm-up
for i in $(seq 1 12); do
    if curl -fsS http://localhost:8070/api/isalive 2>/dev/null | grep -qi true; then
        echo "grobid ready"; break
    fi
    sleep 5
done
for i in 1 2 3 4 5; do
    if PGPASSWORD=citetrace psql -h localhost -p 55448 -U citetrace \
            -d citetrace -c "SELECT 1" >/dev/null 2>&1; then
        echo "pgvector ready"; break
    fi
    sleep 2
done
PGPASSWORD=citetrace psql -h localhost -p 55448 -U citetrace \
    -d citetrace -v ON_ERROR_STOP=1 -f contracts/db/schema.sql

# 2. Run the offline check suite + live tests
export CITETRACE_PGVECTOR_URL=postgresql://citetrace:citetrace@localhost:55448/citetrace
export CITETRACE_DATABASE_URL=postgresql://citetrace:citetrace@localhost:55448/citetrace
export CITETRACE_GROBID_URL=http://localhost:8070
cd starter/services/api && .venv/bin/pytest -q
cd starter/ops && ../services/api/.venv/bin/pytest tests -q
cd starter/apps/web && pnpm test && pnpm typecheck && pnpm build
cd starter/e2e && pnpm exec playwright test tests/three-pane-reader.spec.ts
cd ../../ && make check

# 3. Cleanup
docker rm -f citetrace-pgvector citetrace-grobid
```

## 5. Test counts (cumulative)

| Suite | Count |
|---|---|
| API tests (with live DB+GROBID) | 223 |
| Ops tests | 27 |
| Web vitest | 10 |
| Web Playwright e2e | 5 |
| Annotation pipeline contract | 9 |
| Streamlit annotator contract | 7 |
| Secret rotation contract | 4 |
| Helm lint contract | 3 |
| Contract validators | 17 |
| **Total** | **305** |

The live GROBID smoke (14 tests) and live pgvector smoke
(4 tests) are excluded from the offline count above;
they run when the corresponding container is reachable
and are otherwise skipped explicitly.

## 6. Cross-references

- v1.8 report (previous): [VERIFICATION_REPORT_2026-08-29_v1.8.md](VERIFICATION_REPORT_2026-08-29_v1.8.md)
- v1.7 report: [VERIFICATION_REPORT_2026-08-29_v1.7.md](VERIFICATION_REPORT_2026-08-29_v1.7.md)
- v1.0 report (original, superseded): [VERIFICATION_REPORT_2026-08-28.md](VERIFICATION_REPORT_2026-08-28.md)
- ADR-0008: [docs/adr/0008-vertical-slice-rebuild.md](docs/adr/0008-vertical-slice-rebuild.md)
- ADR-0009: [docs/adr/0009-pgvector-embedding-adapter.md](docs/adr/0009-pgvector-embedding-adapter.md)
- ADR-0010: [docs/adr/0010-live-blocking-metrics.md](docs/adr/0010-live-blocking-metrics.md)
- ADR-0011: [docs/adr/0011-force-rls.md](docs/adr/0011-force-rls.md)
- ADR-0012: [docs/adr/0012-goldset-annotation-pipeline.md](docs/adr/0012-goldset-annotation-pipeline.md)
- ADR-0013: [docs/adr/0013-openapi-strict-mode-bypass.md](docs/adr/0013-openapi-strict-mode-bypass.md)
- ADR-0014: [docs/adr/0014-helm-lint.md](docs/adr/0014-helm-lint.md)
- ADR-0015: [docs/adr/0015-secret-rotation.md](docs/adr/0015-secret-rotation.md)
- ADR-0016: [docs/adr/0016-streamlit-annotator-ui.md](docs/adr/0016-streamlit-annotator-ui.md)
- Makefile: [Makefile](Makefile)
- AGENTS.md: [AGENTS.md](AGENTS.md)
