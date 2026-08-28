# CiteTrace External Source Register

> **Snapshot date:** 2026-08-28  
> **Purpose:** Record external capabilities, versions and policies used as design inputs.  
> **Rule:** Re-check official sources before dependency upgrades, production contracts or legal commitments.

---

## 1. Scholarly parsing and coordinates

### GROBID

- Documentation: https://grobid.readthedocs.io/
- REST service: https://grobid.readthedocs.io/en/latest/Grobid-service/
- Docker: https://grobid.readthedocs.io/en/latest/Grobid-docker/
- PDF coordinates: https://grobid.readthedocs.io/en/latest/Coordinates-in-PDF/
- Upgrade notes: https://grobid.readthedocs.io/en/latest/Upgrading/

**Snapshot:** Official documentation identifies service version 0.9.1 and recommends Docker/web-service operation. Full-text processing can return TEI and selected PDF coordinates. Consolidation can add substantial external-lookup latency.

**Design use:** Isolated parsing service; store raw TEI and normalize into internal domain model. Disable external consolidation in the parser path when CiteTrace's own resolution pipeline is responsible.

---

## 2. Scholarly metadata and graph providers

### Crossref

- REST API: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- Access/authentication: https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/
- API tips: https://www.crossref.org/documentation/retrieve-metadata/rest-api/tips-for-using-the-crossref-rest-api/

**Snapshot:** Public, polite and paid access pools exist; the polite path identifies the client with `mailto`/agent metadata. Rate/concurrency headers and current policy must be honored. Most metadata is broadly reusable, while some abstracts may retain publisher/author rights.

**Design use:** DOI and bibliographic metadata adapter with caching, contact identification and response-policy provenance.

### OpenAlex

- API reference: https://help.openalex.org/api/
- Authentication: https://help.openalex.org/api/authentication/
- Pricing: https://openalex.org/pricing
- Works: https://help.openalex.org/data/works/

**Snapshot:** OpenAlex exposes a connected graph of works, authors, sources, institutions, topics and related entities. In 2026 it uses API-key/budget and usage-based rules that may evolve; adapters must read rate/budget responses and keep pricing outside domain logic.

**Design use:** Work graph, identifiers, citations/references, OA metadata and candidate corroboration.

### Semantic Scholar Academic Graph API

- API documentation: https://api.semanticscholar.org/api-docs/
- Product/API overview: https://www.semanticscholar.org/product/api

**Snapshot:** Provides paper, author, citation and reference graph endpoints with selectable fields. Usage and license requirements must be checked for the intended tier.

**Design use:** Independent candidate/citation graph signal and provider fallback; never single source of truth.

### Unpaywall

- REST API: https://unpaywall.org/products/api
- Data format: https://unpaywall.org/data-format

**Snapshot:** API provides programmatic access to lawful OA-location metadata and requests users remain within published usage guidance (the API page states 100,000 calls/day at this snapshot).

**Design use:** OA location discovery only; final URL still passes CiteTrace security and license/access checks.

---

## 3. Competitive/product inputs

### Scite

- Product: https://scite.ai/
- Reference Check overview: https://scite.ai/blog/reference-check-an-easy-way-to-check-the-reliability-of-your-references-b2afcd64abc6

**Observed capability:** Citation contexts, supporting/contrasting/mentioning classifications and reference checks.

### Elicit

- Product: https://elicit.com/

**Observed capability:** Paper search, extraction, summaries and systematic-review-oriented workflows with evidence links.

### SciSpace

- Product: https://scispace.com/

**Observed capability:** Paper search, PDF interaction, literature review and research assistance.

### ResearchRabbit

- Product: https://www.researchrabbit.ai/

**Observed capability:** Citation-network discovery and visual research maps.

**Design implication:** Search, PDF chat, generic summary and citation graph are not sufficient differentiation. CiteTrace centers exact cross-paper evidence, scope-aware verification, transformation and provenance.

---

## 4. Evaluation research inputs

### SciCite

- Repository: https://github.com/allenai/scicite
- Paper: https://aclanthology.org/N19-1361/

**Use:** Citation-intent taxonomy and evaluation reference; CiteTrace taxonomy is expanded and multi-label.

### MultiCite

- Paper/search record: https://aclanthology.org/2022.naacl-main.86/

**Use:** Multi-sentence and multi-label citation-context considerations.

### Scientific claim verification

- SciFact paper: https://aclanthology.org/2020.emnlp-main.609/
- FEVER-related scientific verification literature and current primary research should be reviewed during model selection.

**Design implication:** LLM output is evaluated through retrieval and verification stages rather than treated as inherently reliable.

---

## 5. Runtime technology snapshot

### Web

- Next.js security release: https://nextjs.org/blog/august-2026-security-release
- Next.js blog: https://nextjs.org/blog
- React versions: https://react.dev/versions
- PDF.js: https://mozilla.github.io/pdf.js/

**Pinned baseline:** Next.js 16.3.3 due to the August 25, 2026 security release; React 19.2.x. Keep exact patch versions in lockfiles and follow security advisories.

### API/runtime

- FastAPI release notes: https://fastapi.tiangolo.com/release-notes/
- Python 3.13.15: https://www.python.org/downloads/release/python-31315/
- Node releases: https://nodejs.org/en/about/previous-releases

**Pinned baseline:** FastAPI 0.141.1, Python 3.13.x, Node.js 24 LTS. Python 3.13 is selected conservatively for ecosystem compatibility even though a newer feature series exists.

### Data and queue

- PostgreSQL releases: https://www.postgresql.org/docs/release/
- PostgreSQL 18.6 announcement: https://www.postgresql.org/about/news/postgresql-186-1711-1615-1519-1424-and-19-beta-3-released-3365/
- pgvector: https://github.com/pgvector/pgvector
- pgvector changelog: https://github.com/pgvector/pgvector/blob/master/CHANGELOG.md
- Redis 8 docs: https://redis.io/docs/latest/develop/whats-new/8-0/
- Redis licenses: https://redis.io/legal/licenses/

**Pinned baseline:** PostgreSQL 18.6 and pgvector 0.8.6. Redis 8.x is used as a replaceable queue/cache dependency; review its available license choice and exact image before commercial deployment.

### Package manager and observability

- pnpm releases: https://pnpm.io/blog
- OpenTelemetry: https://opentelemetry.io/docs/

**Pinned baseline:** pnpm 11.24 in the starter for conservative availability; pnpm 12 became stable on August 26, 2026 and should be adopted only after CI/tooling validation. OpenTelemetry is the observability abstraction.

---

## 6. Legal/source register actions before production

- confirm each provider's current API/license/attribution terms,
- document commercial tier and rate-limit requirements,
- decide Redis license option or managed alternative,
- perform publisher/repository-specific review for stored/displayed excerpts,
- record model-provider data retention/training settings,
- confirm regional privacy and institutional requirements,
- establish takedown and source-correction process.
