# CiteTrace AAA Development Package v1.0

> **Working codename:** CiteTrace  
> **Package date:** 2026-08-28  
> **Status:** Product blueprint + implementation-ready contracts + runnable foundation scaffold  
> **Primary language:** Korean documentation, English code/contracts

한국어 시작 안내는 [`START_HERE_KO.md`](START_HERE_KO.md)에서 확인할 수 있습니다.

CiteTrace is an **evidence-first citation intelligence agent**. A user uploads or links a scientific paper, clicks an in-text citation, and receives a traceable explanation of:

1. why the citation appears at that location,
2. which exact passage, figure, table, result, or method in the cited work supports it,
3. whether the source directly supports, partially supports, contradicts, or fails to justify the citing claim,
4. what the current paper adopted, changed, extended, simplified, or transferred,
5. how confident the system is at each stage, and
6. which evidence the user should inspect before trusting the conclusion.

The product is intentionally **not** positioned as another generic “chat with PDF,” paper search, or one-paragraph summarizer. Its core promise is **claim-to-source traceability with explicit uncertainty and provenance**.

---

## 1. Package contents

| Path | Purpose |
|---|---|
| `docs/00_MASTER_BLUEPRINT.md` | Single source of truth for the product and system |
| `docs/01_PRODUCT_REQUIREMENTS_PRD.md` | Product requirements, users, journeys, stories, acceptance rules |
| `docs/02_COMPETITIVE_STRATEGY.md` | Market position, differentiation, moat, anti-features |
| `docs/03_DOMAIN_TAXONOMY.md` | Citation intent, evidence relation, transformation, confidence taxonomy |
| `docs/04_SYSTEM_ARCHITECTURE.md` | Runtime architecture, components, boundaries, deployment topology |
| `docs/05_AGENT_AI_PIPELINE.md` | Agent graph, retrieval, verification, abstention, prompt-injection defenses |
| `docs/06_DATA_MODEL_PROVENANCE.md` | Entities, provenance chain, versioning, coordinates, confidence model |
| `docs/07_API_EVENT_CONTRACTS.md` | REST resources, events, idempotency, errors, compatibility rules |
| `docs/08_UX_UI_SPEC.md` | Three-pane reader, evidence cards, graph, states, accessibility |
| `docs/09_EVALUATION_GOLDSET_QA.md` | Gold set, metrics, gates, red-team and release evaluation |
| `docs/10_SECURITY_PRIVACY_COPYRIGHT.md` | Threat model, tenant isolation, retention, legal acquisition rules |
| `docs/11_DEVOPS_SRE_COST.md` | Environments, observability, SLOs, backpressure, cost controls |
| `docs/12_ROADMAP_BACKLOG.md` | Sequenced vertical slices and backlog with exit gates |
| `docs/13_RISK_REGISTER.md` | Product, technical, legal, quality, operational risks and controls |
| `docs/14_GTM_METRICS.md` | Launch wedge, pricing hypotheses, activation/retention/quality metrics |
| `docs/15_PROMPT_PACK_GUIDE.md` | Prompt architecture, schemas, routing, evaluation and change control |
| `docs/16_TEAM_OPERATING_MODEL.md` | Roles, rituals, decision records, definition of ready/done |
| `docs/17_DEMO_PITCH.md` | Demo script, pitch narrative, failure-safe demo path |
| `docs/18_ACCEPTANCE_CHECKLIST.md` | End-to-end launch and handoff checklist |
| `docs/19_SOURCE_REGISTER_2026-08-28.md` | External official sources and dated assumptions |
| `docs/20_LICENSE_AND_THIRD_PARTY_POLICY.md` | Repository/content license and SBOM decision gate |
| `docs/21_REQUIREMENTS_TRACEABILITY_MATRIX.md` | PRD-to-plan-to-test release traceability |
| `docs/adr/` | Architecture Decision Records |
| `docs/superpowers/specs/` | Approved product/system design specification |
| `docs/superpowers/plans/` | Four implementation plans with exact tasks, tests, and commits |
| `contracts/openapi.yaml` | Phase-0 REST contract; later resources are added contract-first by milestone |
| `contracts/event_catalog.yaml` | Event topics and payload contracts |
| `contracts/db/schema.sql` | PostgreSQL + pgvector schema and RLS foundation |
| `contracts/schemas/` | JSON Schemas for analysis, evidence, provenance and feedback |
| `contracts/examples/` | Executable valid/abstained result and feedback examples |
| `contracts/taxonomies/` | Machine-readable controlled vocabularies |
| `prompts/` | Versioned, schema-bound prompt pack |
| `config/` | Model routing, source policy and retention examples |
| `eval/` | Gold-set template, synthetic cases, rubric and evaluation guidance |
| `starter/` | Runnable FastAPI foundation, web shell, Docker dependencies, CI |
| `starter/DEPENDENCY_LOCKING.md` | Mandatory lockfile, digest and SBOM bootstrap gate |
| `IMPLEMENTATION_META_PROMPT.md` | Master prompt for coding agents executing the package |
| `AGENTS.md` | Repository-level working rules for human and AI contributors |
| `CONTRIBUTING.md`, `SECURITY.md` | Change workflow and security disclosure/deployment baseline |
| `VERIFICATION_REPORT_2026-08-28.md` | Reproducible checks, results and environment limitations |
| `VERIFICATION_REPORT_2026-08-29_v1.11.md` | v1.1–v1.11 verification record (the current state) |

---

## 2. Recommended reading order

### Founder / product owner

1. `docs/00_MASTER_BLUEPRINT.md`
2. `docs/01_PRODUCT_REQUIREMENTS_PRD.md`
3. `docs/02_COMPETITIVE_STRATEGY.md`
4. `docs/12_ROADMAP_BACKLOG.md`
5. `docs/14_GTM_METRICS.md`

### Engineering lead

1. `docs/00_MASTER_BLUEPRINT.md`
2. `docs/04_SYSTEM_ARCHITECTURE.md`
3. `docs/05_AGENT_AI_PIPELINE.md`
4. `docs/06_DATA_MODEL_PROVENANCE.md`
5. `docs/07_API_EVENT_CONTRACTS.md`
6. `docs/superpowers/plans/README.md`

### ML / research engineer

1. `docs/03_DOMAIN_TAXONOMY.md`
2. `docs/05_AGENT_AI_PIPELINE.md`
3. `docs/09_EVALUATION_GOLDSET_QA.md`
4. `docs/15_PROMPT_PACK_GUIDE.md`
5. `eval/README.md`

### Security / legal reviewer

1. `docs/10_SECURITY_PRIVACY_COPYRIGHT.md`
2. `docs/06_DATA_MODEL_PROVENANCE.md`
3. `docs/11_DEVOPS_SRE_COST.md`
4. `docs/13_RISK_REGISTER.md`

---

## 3. Foundation scaffold quick start

The scaffold proves the initial API and domain contract. It does **not** pretend to be the finished evidence engine.

### Requirements

- Python 3.13+
- Docker Engine with Compose v2
- Node.js 24 LTS and pnpm 11+ for the web shell

### Start dependencies

```bash
cd starter
docker compose up -d postgres redis grobid
```

### Run API tests

```bash
cd starter/services/api
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

### Run API

```bash
uvicorn citetrace_api.main:app --reload --port 8000
```

### Run web shell

```bash
cd starter/apps/web
pnpm install
pnpm dev
```

---

## 4. Verify the build

```bash
make check
```

The `make check` target at the repository root runs every
offline check: 17/17 contract validators, 223 API tests
(with live DB and GROBID URLs set), 27 ops tests
(runbook/Kubernetes/secret-rotation/helm-lint), 10 web
unit tests, the production Next.js build, and the
release-evaluation script. With `helm` on PATH the
target also runs `helm lint` against the production
chart. The complete verified state is recorded in
`VERIFICATION_REPORT_2026-08-29_v1.11.md`.

The `make check` target exit 0 means every offline check
passes. The release pipeline additionally runs the
`pgvector-smoke` and `grobid-smoke` CI jobs against real
Docker containers.

### Helm chart (Slice 16)

```bash
helm lint starter/ops/release/helm
helm template citetrace starter/ops/release/helm | head -50
```

The chart in `starter/ops/release/helm/` produces 3
Deployments (api, web, worker) under the default
`values.yaml`. The templates pin the securityContext,
the secret references, and the resources; ADR-0014
documents the production release path.

### Secret rotation gate (Slice 17)

The secret boundary file
(`starter/ops/policies/secret_manager_boundary.yaml`)
declares six production secrets with explicit
`rotation_days` values. `scripts/check_secret_rotation.py`
asserts, for each secret, that the
`CITETRACE_SECRET_AGE_<NAME>` environment variable is
below the declared `rotation_days`:

```bash
# in CI: exit 0 = all within window, 1 = overdue, 2 = env unset
CITETRACE_SECRET_AGE_DATABASE_URL=10 \
CITETRACE_SECRET_AGE_REDIS_URL=10 \
CITETRACE_SECRET_AGE_MODEL_PROVIDER_API_KEY=10 \
CITETRACE_SECRET_AGE_SENTRY_DSN=10 \
CITETRACE_SECRET_AGE_GROBID_SHARED_SECRET=10 \
CITETRACE_SECRET_AGE_TENANT_ENCRYPTION_KEY=10 \
    python scripts/check_secret_rotation.py
```

The gate is informational in `make check` and becomes a
real gate when the deployment wires the
`CITETRACE_SECRET_AGE_<NAME>` environment from a real
secret manager.

### Cut a release

The release tool refuses to run on a dirty working tree
and refuses to push a tag the user did not author:

```bash
git tag -a v1.8.0 -m 'v1.8.0 release notes'
make release VERSION=v1.8.0
```

The `make release` target runs `make check` first; if any
offline check fails the release is aborted. On success the
target pushes the tag and creates a GitHub release whose
body is the new CHANGELOG section. The `gh` CLI is
required.

### Live integration smokes (optional, requires Docker)

The CI `grobid-smoke` and `pgvector-smoke` jobs run
real-container integration tests that the offline
`make check` cannot exercise:

```bash
# GROBID
docker run -d --rm -p 8070:8070 grobid/grobid:0.9.1-crf
sleep 45  # JVM warm-up
curl -fsS http://localhost:8070/api/isalive
CITETRACE_GROBID_URL=http://localhost:8070 \
  pytest -q starter/services/api/tests/test_grobid_live_smoke.py \
              starter/services/api/tests/test_grobid_robustness.py

# pgvector
docker run -d --rm -p 55445:5432 \
  -e POSTGRES_DB=citetrace -e POSTGRES_USER=citetrace \
  -e POSTGRES_PASSWORD=citetrace pgvector/pgvector:pg18
PGPASSWORD=citetrace psql -h localhost -p 55445 -U citetrace -d citetrace \
  -v ON_ERROR_STOP=1 -f contracts/db/schema.sql
CITETRACE_PGVECTOR_URL=postgresql://citetrace:citetrace@localhost:55445/citetrace \
  pytest -q starter/services/api/tests/test_pgvector_search.py \
              starter/services/api/tests/test_rls_force_and_cross_tenant.py \
              starter/services/api/tests/test_live_blocking_metrics.py
```

## 5. Annotation pipeline (Slice 14)

The 300-case human gold set is the next blocker for a
"first credible release". The annotation pipeline
(`ADR-0012`) provides:

```bash
# 1. start a 5-case pilot
python scripts/annotate.py init \
  --case-ids pilot-001,pilot-002,pilot-003,pilot-004,pilot-005 \
  --output eval/pilot.jsonl

# 2. edit the JSONL (or convert to CSV, edit, convert back)
python scripts/build_goldset.py jsonl-to-csv \
  --jsonl eval/pilot.jsonl --csv eval/pilot.csv

# 3. validate before submit
python scripts/annotate.py validate --input eval/pilot.jsonl

# 4. measure IAA between two annotators
python scripts/compute_iaa.py --a annotator-a.jsonl --b annotator-b.jsonl

# 5. adjudicate
python scripts/adjudicate.py \
  --a annotator-a.jsonl --b annotator-b.jsonl \
  --adjudicator adjudicator.jsonl \
  --output eval/adjudicated.jsonl \
  --ties eval/ties.jsonl
```

The release gate refuses to pass on the synthetic seed
alone; the 300-case human gold set is required.

A domain expert can drive the same flow from a web UI
(Slice 18, `ADR-0016`):

```bash
pip install streamlit jsonschema
streamlit run scripts/annotate_ui.py
```

The UI re-validates every row against the JSON Schema on
save; an invalid field blocks the write and shows a red
error message under the offending field. The committed
pilot (`eval/pilot_annotation/`) demonstrates the loop
end-to-end: alice and bob disagree on two cases (κ = 0.52
between them on `gold_evidence_relation`); ada's adjudicator
file resolves every disagreement and produces a 5-row
merged file with 0 ties.

## 6. Maturity boundary (v1.11)

This package includes a complete target design, executable
contract scaffold, testable interfaces, evaluation pipeline,
implementation sequence, and the v1.1–v1.11 slice rebuild
(18 slices, 9 ADRs, 12 tags, 305 tests pass, `make check`
exit 0). It does **not** include:

- 300 human-annotated gold-set cases (the infrastructure
  is in place — the JSON Schema, the four CLI scripts,
  and the Streamlit annotator UI all ship; the cases
  are a multi-week
  human-in-the-loop activity);
- production credentials for external scholarly APIs;
- commercial legal advice or publisher-specific licensing
  agreements;
- a fully implemented PDF coordinate renderer;
- a production cloud account or deployed infrastructure.

These are intentionally represented as concrete
implementation and operating work in the included plans
rather than falsely presented as complete.

---

## 7. Non-negotiable product principles

1. **Evidence before explanation.** The system retrieves and stores evidence before generating prose.
2. **No invented quotations.** Every displayed quote must be byte/character-span anchored to a retained source asset.
3. **No paywall bypass.** Full text is processed only from user-authorized uploads or lawful access paths.
4. **Uncertainty is a feature.** The UI exposes stage-level confidence and a reason for abstention.
5. **Version everything.** Source assets, parsers, models, prompts, taxonomies and generated results are versioned.
6. **LLM output is not ground truth.** Deterministic extraction, retrieval, validation and human feedback constrain model output.
7. **Private uploads remain private.** User documents are not used to train shared models by default.
8. **Start narrow.** Initial quality is optimized for born-digital English scientific PDFs rather than claiming universal document support.

## Release history (v1.x)

The package is versioned with conventional semantic
versioning. Every release tag corresponds to a `make check`
exit 0 against the committed code.

| Tag | Date | Theme | Slices | Tests |
|---|---|---|---|---|
| v1.0.0 | 2026-08-28 | Initial baseline | — | (baseline) |
| v1.1.0 | 2026-08-29 | Dead-asset cleanup + honest eval | 1–2 | 122 + 3 |
| v1.2.0 | 2026-08-29 | pgvector + embedding adapter | 9 | 138 + 4 |
| v1.3.0 | 2026-08-29 | Live blocking-metric collection | 10 | 138 + 4 |
| v1.4.0 | 2026-08-29 | GROBID robustness | 11 | 148 + 10 |
| v1.5.0 | 2026-08-29 | Next.js full build + Playwright | 12 | 148 + 10 + 5 |
| v1.6.0 | 2026-08-29 | RLS force + cross-tenant | 13 | 154 + 6 |
| v1.7.0 | 2026-08-29 | Human-annotated gold-set pipeline | 14 | 160 + 9 |
| v1.8.0 | 2026-08-29 | `make check` fully green | 15 | 218 |
| v1.9.0 | 2026-08-29 | Helm chart templates | 16 | 221 + 3 |
| v1.10.0 | 2026-08-29 | Secret rotation enforcement | 17 | 221 + 4 |
| v1.11.0 | 2026-08-29 | Streamlit annotator UI | 18 | 232 + 7 |
| v1.11.1 | 2026-08-29 | Docs polish + helm icon | — | 232 |

The 18 vertical slices (v1.1.0–v1.11.0) and 9 ADRs (0008–0016)
are listed in `VERIFICATION_REPORT_2026-08-29_v1.11.md`.

---

## 8. Package maturity boundaries

This package includes a complete target design, executable contract scaffold, testable interfaces, evaluation plan and implementation sequence. It does not include:

- production credentials for external scholarly APIs,
- commercial legal advice or publisher-specific licensing agreements,
- a trained proprietary citation-verification model,
- a fully implemented PDF coordinate renderer,
- an annotated 300–500-case human gold set,
- a production cloud account or deployed infrastructure.

Those are intentionally represented as concrete implementation and operating work in the included plans rather than falsely presented as complete.

---

## 9. Versioning and change control

- Product specification version: `1.0.0`
- Public API baseline: `v1`
- Event contract baseline: `1.0`
- Prompt pack baseline: `2026-08-28.1`
- Taxonomy baseline: `1.0.0`
- Database migration baseline: `0001`

Any change that alters evidence semantics, confidence calculation, source-access policy, user-visible interpretation, or API compatibility requires an ADR and evaluation comparison against the locked regression suite.
