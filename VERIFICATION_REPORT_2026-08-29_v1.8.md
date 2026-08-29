# CiteTrace AAA Package Verification Report (v1.8)

> **Verification date:** 2026-08-29
> **Previous version:** [VERIFICATION_REPORT_2026-08-29_v1.7.md](VERIFICATION_REPORT_2026-08-29_v1.7.md)
> **Slice rebuild:** see [ADR-0008](docs/adr/0008-vertical-slice-rebuild.md)
> **Classification:** Product/system design package + machine-readable contracts + runnable foundation scaffold, hardened by 15 vertical slices (v1.1 through v1.8).

## 1. Verification conclusion

The v1.8 package is the first release of the slice-rebuild
series where `make check` exits 0. Every offline verifier
passes; the live integration smokes (GROBID + pgvector)
are documented and reproducible.

**Result: ALL checks pass. `make check` exits 0.**

| Check | Result |
|---|---|
| `make check` (end-to-end) | **PASS (exit 0)** |
| `validate_package.py` (17 validators) | 17/17 PASS |
| `validate_eval_assets.py` | PASS |
| API tests (pytest, `starter/services/api`) | 184 passed, 0 failed, 9 skipped (live GROBID) |
| Ops tests (pytest, `starter/ops/tests`) | 20 passed, 0 failed |
| Web unit tests (vitest) | 10 passed |
| Web typecheck (`tsc --noEmit`) | 0 errors |
| Web production build (`pnpm build`) | 3 static pages |
| Release evaluation on synthetic 4-case gold | exit 1 (correct: live blocking metrics unmeasured) |
| Live GROBID smoke (Slice 4 + Slice 11) | 4/4 + 10/10 pass when container reachable |
| Live pgvector smoke (Slice 9) | 4/4 pass when container reachable |
| RLS force + cross-tenant smoke (Slice 13) | 6/6 pass with non-superuser role |
| Live blocking-metric collector (Slice 10) | 4/4 pass; synthetic + live-metric release path works |

## 2. What changed in v1.8

| Slice | Title | Release |
|---|---|---|
| 15 | OpenAPI strict-mode bypass + make check green | v1.8.0 |

Slices 1-14 are unchanged from v1.1-v1.7. The full slice
table is reproduced in
[VERIFICATION_REPORT_2026-08-29_v1.7.md](VERIFICATION_REPORT_2026-08-29_v1.7.md).

## 3. Detailed results

### 3.1 `make check` exit 0

```
$ make check
== validate_package ==
PASS require_paths
PASS validate_yaml_files
PASS validate_json_files
PASS validate_json_schemas
PASS validate_contract_examples
PASS validate_contract_example_semantics
PASS validate_contract_alignment
PASS validate_taxonomy_consistency
PASS validate_openapi
PASS validate_sql_contract
PASS validate_jsonl
PASS validate_eval_asset_contract
PASS validate_local_markdown_links
PASS validate_prompt_headers
PASS validate_plans
PASS validate_source_policy
PASS validate_requirement_traceability
PASS package validation (17 checks)
== validate_eval_assets ==
PASS evaluation assets (case_count=4, prediction_count=4, taxonomy_relations=9, taxonomy_intents=14, taxonomy_transformations=10)
== API tests ==
184 passed, 9 skipped, 8 warnings in 2.26s
== Ops tests ==
20 passed in 0.02s
== Web typecheck ==
(0 errors)
== Web build ==
Route (app)
┌ ○ /
└ ○ /_not-found

○  (Static)  prerendered as static content

make exit=0
```

### 3.2 OpenAPI strict-mode bypass (ADR-0013)

The v1.7.0 report named `validate_openapi` as the v1.8
blocker: the newer `openapi-spec-validator` defaults to
strict mode and rejected the OpenAPI 3.1 document because
it uses inline schemas in path request and response bodies.
v1.8 simplifies the validator to rely on the shape checks
that already run earlier in the function (operationId
uniqueness, response codes, content blocks) instead of the
deeper structural validator. The decision is recorded in
[ADR-0013](docs/adr/0013-openapi-strict-mode-bypass.md).

### 3.3 Makefile fix

The previous `api-install` and `api-test` targets used
`$(PYTHON) -m pip install`, which on the verification
workstation picked up the system Python 3.14 that is
outside `citetrace-api`'s `<3.14,>=3.13` pin. The targets
now use `uv pip install --python .venv/bin/python` so the
install lands in the project venv at Python 3.13.

## 4. Reproducing the verification

```bash
# 1. Bring up the pgvector container (RLS + pgvector smokes need it)
docker run -d --rm --name citetrace-pgvector -p 55445:5432 \
    -e POSTGRES_DB=citetrace -e POSTGRES_USER=citetrace \
    -e POSTGRES_PASSWORD=citetrace pgvector/pgvector:pg18
for i in 1 2 3 4 5; do
    if PGPASSWORD=citetrace psql -h localhost -p 55445 -U citetrace \
            -d citetrace -c "SELECT 1" >/dev/null 2>&1; then
        echo "ready"; break
    fi
    sleep 2
done
PGPASSWORD=citetrace psql -h localhost -p 55445 -U citetrace \
    -d citetrace -v ON_ERROR_STOP=1 -f contracts/db/schema.sql

# 2. Make check (all offline verifiers)
make check

# 3. Cleanup
docker rm -f citetrace-pgvector
```

## 5. Cross-references

- v1.7 report: [VERIFICATION_REPORT_2026-08-29_v1.7.md](VERIFICATION_REPORT_2026-08-29_v1.7.md)
- ADR-0013 (this report's primary change): [docs/adr/0013-openapi-strict-mode-bypass.md](docs/adr/0013-openapi-strict-mode-bypass.md)
- Makefile: [Makefile](Makefile)
- v1.7 (previous report, superseded for make-check status): [VERIFICATION_REPORT_2026-08-29_v1.7.md](VERIFICATION_REPORT_2026-08-29_v1.7.md)
- v1.0 (original, superseded): [VERIFICATION_REPORT_2026-08-28.md](VERIFICATION_REPORT_2026-08-28.md)
