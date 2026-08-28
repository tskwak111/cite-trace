# CiteTrace AAA Package Verification Report

> **Verification date:** 2026-08-28  
> **Package:** `CiteTrace_AAA_Development_Package_v1.0`  
> **Classification:** Product/system design package + machine-readable contracts + runnable foundation scaffold. This is **not** a completed production service.

## 1. Verification conclusion

The package passed every check that can be executed in the current offline container without downloading dependencies or starting external infrastructure:

- package/document/contract validation: **17/17 checks passed**;
- FastAPI foundation tests in the available Python environment: **11/11 tests passed**;
- Python bytecode compilation: **passed**;
- TypeScript/TSX syntax parse: **5/5 source files passed**;
- evaluation asset contract validation: **passed**;
- bundled synthetic prediction scorer: **passed its four contract examples**;
- JSON Schema examples, exact quote hashes/offsets, provenance references, taxonomy alignment, OpenAPI local references, SQL structure/RLS requirements, prompt headers, plan structure and PRD traceability: **passed**.

Three production-grade checks could not be completed in this environment:

1. exact Python dependency resolution and test execution under the pinned FastAPI version;
2. Next.js dependency installation, full typecheck and production build under the required Node/pnpm versions;
3. execution of the PostgreSQL schema against a live PostgreSQL 18 instance.

Those are explicit bootstrap gates, not hidden success claims. The exact reproduction commands are recorded below.

## 2. Environment observed

| Component | Available environment | Package target | Verification meaning |
|---|---:|---:|---|
| Python | 3.13.5 | `>=3.13,<3.14` | Version family matches |
| FastAPI | 0.128.2 | 0.141.1 | Foundation tests passed on an older available version; exact pin not tested |
| Pydantic | 2.13.4 | `>=2.11,<3` | Target range matches |
| pytest | 9.0.2 | `>=8.4,<9` | Tests passed, but available pytest is outside the intended dev range |
| Node.js | 22.16.0 | `>=24,<25` | Does not meet target runtime |
| npm | 10.9.2 | Supporting only | Present |
| global TypeScript | 5.8.3 | project `^5.9.0` | Used only for syntax parsing; exact project compiler not installed |
| uv | 0.10.0 | bootstrap tool | Present |
| pnpm | not installed | 11.24.0 | Full web install/build unavailable |
| Docker | not installed | Compose dependencies | Integration infrastructure unavailable |
| psql | not installed | PostgreSQL 18 | SQL execution unavailable |
| ruff | not installed | project dev dependency | Lint unavailable |
| mypy | not installed | project dev dependency | Strict typecheck unavailable |
| openapi-spec-validator | not installed | optional secondary validation | Internal OpenAPI validation ran; external validator unavailable |

## 3. Commands executed and results

### 3.1 Package and contract validation

```bash
python scripts/validate_package.py
```

Result:

```text
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
```

This check verifies, among other things:

- required architecture, product, security, evaluation and implementation documents exist;
- every YAML/JSON file parses;
- Draft 2020-12 JSON Schemas are valid;
- four executable examples validate against their schemas;
- quote hashes, offsets, provenance assets and supporting span references are internally consistent;
- EvidenceLink/Provenance fields align across OpenAPI and JSON Schema;
- citation intent, evidence relation, transformation and feedback taxonomy values align across taxonomy files, OpenAPI, JSON Schema and PostgreSQL enums;
- every local OpenAPI `$ref` resolves and every operation ID is present and unique;
- local Markdown document links resolve after code blocks and external links are excluded;
- required PostgreSQL tables, transaction boundary and forced RLS declarations exist;
- prompt templates are versioned and enforce schema-bound JSON output;
- four plans contain contiguous tasks, exact workflow markers and no prohibited placeholders;
- source policy prohibits paywall bypass and private-network fetches;
- every PRD requirement is represented in the traceability matrix.

### 3.2 API foundation tests

```bash
PYTHONPATH=starter/services/api/src pytest -q starter/services/api/tests
```

Result:

```text
...........                                                              [100%]
11 passed
```

Covered behavior:

- health endpoint;
- analysis creation, retrieval and cancellation;
- same-body idempotent replay;
- conflict on reused key with a different body;
- unknown-field rejection and Problem Details response;
- exact quote, offset and SHA-256 validation;
- workflow transition acceptance/rejection and terminal timestamps.

Important boundary: these tests used FastAPI 0.128.2 and pytest 9.0.2 already available in the container. They do not substitute for a clean run using the package pins.

### 3.3 Python compilation

```bash
python -m compileall -q \
  starter/services/api/src \
  starter/services/api/tests \
  scripts
```

Result: exit code `0`.

### 3.4 TypeScript/TSX syntax validation

```bash
node scripts/validate_typescript_syntax.js
```

Result:

```text
PASS TypeScript syntax (5 files)
```

This parses the source with the available global TypeScript compiler. It is not a substitute for module-aware typechecking or a Next.js production build.

### 3.5 Evaluation assets

```bash
python scripts/validate_eval_assets.py
```

Result:

```text
PASS evaluation assets (
  case_count=4,
  prediction_count=4,
  taxonomy_relations=9,
  taxonomy_intents=14,
  taxonomy_transformations=10
)
```

The check validates sample/gold IDs, required fields, taxonomy values, source-span references, inaccessible-source abstention behavior, canonical CSV headers and mandatory release-blocking rubric metrics.

### 3.6 Synthetic scorer

```bash
python scripts/score_sample_predictions.py \
  --gold eval/sample_cases.jsonl \
  --predictions eval/sample_predictions.jsonl
```

Result:

```json
{
  "case_count": 4,
  "citation_intent_set_f1": 1.0,
  "extra_case_ids": [],
  "missing_case_ids": [],
  "relation_accuracy": 1.0,
  "transformation_set_f1": 1.0,
  "unsupported_material_statement_rate": 0.0
}
```

These are deliberately constructed **synthetic contract examples**. They demonstrate scorer and schema behavior only and must never be reported as model quality, benchmark performance or scientific validity.

## 4. Checks attempted but not claimable as passed

### 4.1 Exact API dependency environment

Command:

```bash
cd starter/services/api
UV_OFFLINE=1 uv sync --all-extras
```

Result: dependency resolution stopped because the offline cache did not contain `fastapi==0.141.1`. No network package installation was available. Therefore, exact pinned dependency tests, Ruff and mypy are pending.

Required clean-environment gate:

```bash
cd starter/services/api
uv lock
uv sync --all-extras --frozen
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

Commit the generated `uv.lock` only after reviewing its resolved packages and hashes.

### 4.2 Web typecheck and production build

Attempted command:

```bash
tsc --noEmit -p starter/apps/web/tsconfig.json
```

Result: failed because `next`, `react`, their type packages and `react/jsx-runtime` were not installed. The environment also has Node 22 while the package requires Node 24 and has no pnpm. This result does not identify a verified application type error; it establishes that dependency-aware typechecking was not possible.

Required clean-environment gate:

```bash
corepack enable
cd starter/apps/web
pnpm install
pnpm typecheck
pnpm build
```

After the first trusted install, commit `pnpm-lock.yaml`, use `pnpm install --frozen-lockfile` in CI and pin production image digests as described in `starter/DEPENDENCY_LOCKING.md`.

### 4.3 PostgreSQL and Compose integration

Docker and `psql` are absent. The SQL contract received structural/RLS validation but was not executed by PostgreSQL.

Required gate:

```bash
cd starter
docker compose up -d postgres redis grobid
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f ../contracts/db/schema.sql
```

Then run tenant-isolation, vector-index, check-constraint, migration upgrade/downgrade and outbox integration tests from the implementation plans.

### 4.4 Secondary OpenAPI validation

The internal validator checked OpenAPI 3.1 version, local references and operation IDs, and JSON Schema examples were validated with `jsonschema`. The optional `openapi-spec-validator` package was not installed. Run it in the locked dev environment as an additional independent check.

## 5. Maturity and claim boundary

### Included and verified as package assets

- approved product/system design specification;
- comprehensive master blueprint and PRD;
- competitive strategy and product moat;
- architecture, data/provenance, agent graph and UI specifications;
- security, privacy, copyright, SRE, cost and team operating plans;
- controlled taxonomies and versioned prompt pack;
- OpenAPI, event, PostgreSQL and JSON Schema contracts;
- executable contract examples;
- evaluation handbook, rubric, template and synthetic checks;
- four implementation plans with TDD steps and acceptance gates;
- foundation API and three-pane reader scaffold;
- dependency-locking and CI bootstrap policy;
- requirements traceability matrix and source register.

### Deliberately not claimed

- production-ready citation analysis;
- implemented GROBID ingestion, metadata-provider adapters or lawful full-text acquisition;
- working hybrid retrieval/reranking or LLM relation verifier;
- a human-adjudicated 300–500-case gold set;
- exact pinned API lint/typecheck;
- built Next.js production artifact;
- live database migration and RLS proof;
- cloud deployment, production SLO evidence or security audit;
- real-world model performance.

The `starter/` directory is a tested foundation and interface demonstration. The four plans describe the remaining implementation work necessary to turn the package into a production service.

## 6. Clean-environment release checklist

Before any production-readiness claim:

1. Generate and commit reviewed Python and pnpm lockfiles.
2. Pin OCI images by digest and produce CycloneDX or SPDX SBOMs.
3. Run Ruff, strict mypy, exact-pinned pytest, web typecheck and Next production build.
4. Apply the database schema to PostgreSQL 18 and test every RLS policy with at least two workspaces.
5. Execute GROBID, source-provider and object-storage integrations against recorded lawful fixtures.
6. Complete all four implementation plans in order.
7. Build and adjudicate the minimum gold set in `eval/README.md`.
8. Pass every blocking metric in `eval/rubric.yaml`, including zero fabricated quotes and zero cross-tenant disclosures.
9. Run SAST, dependency/license scanning, secret scanning, container scanning and threat-model review.
10. Run E2E, load, cancellation, retry, disaster-recovery and deletion/retention tests.

## 7. Reproducible baseline command set

From the package root, the checks that do not require new downloads are:

```bash
python scripts/validate_package.py
PYTHONPATH=starter/services/api/src pytest -q starter/services/api/tests
python -m compileall -q starter/services/api/src starter/services/api/tests scripts
node scripts/validate_typescript_syntax.js
python scripts/validate_eval_assets.py
python scripts/score_sample_predictions.py \
  --gold eval/sample_cases.jsonl \
  --predictions eval/sample_predictions.jsonl
```

The authoritative full bootstrap and locking sequence is in `starter/DEPENDENCY_LOCKING.md`; milestone-specific verification is in the four files under `docs/superpowers/plans/`.
