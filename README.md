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

Open `http://localhost:3000`; API documentation is available at `http://localhost:8000/docs`.

---

## 4. Non-negotiable product principles

1. **Evidence before explanation.** The system retrieves and stores evidence before generating prose.
2. **No invented quotations.** Every displayed quote must be byte/character-span anchored to a retained source asset.
3. **No paywall bypass.** Full text is processed only from user-authorized uploads or lawful access paths.
4. **Uncertainty is a feature.** The UI exposes stage-level confidence and a reason for abstention.
5. **Version everything.** Source assets, parsers, models, prompts, taxonomies and generated results are versioned.
6. **LLM output is not ground truth.** Deterministic extraction, retrieval, validation and human feedback constrain model output.
7. **Private uploads remain private.** User documents are not used to train shared models by default.
8. **Start narrow.** Initial quality is optimized for born-digital English scientific PDFs rather than claiming universal document support.

---

## 5. Package maturity boundaries

This package includes a complete target design, executable contract scaffold, testable interfaces, evaluation plan and implementation sequence. It does not include:

- production credentials for external scholarly APIs,
- commercial legal advice or publisher-specific licensing agreements,
- a trained proprietary citation-verification model,
- a fully implemented PDF coordinate renderer,
- an annotated 300–500-case human gold set,
- a production cloud account or deployed infrastructure.

Those are intentionally represented as concrete implementation and operating work in the included plans rather than falsely presented as complete.

---

## 6. Versioning and change control

- Product specification version: `1.0.0`
- Public API baseline: `v1`
- Event contract baseline: `1.0`
- Prompt pack baseline: `2026-08-28.1`
- Taxonomy baseline: `1.0.0`
- Database migration baseline: `0001`

Any change that alters evidence semantics, confidence calculation, source-access policy, user-visible interpretation, or API compatibility requires an ADR and evaluation comparison against the locked regression suite.
