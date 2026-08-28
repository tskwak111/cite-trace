# CiteTrace Reference Resolution and Source Acquisition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve every extracted bibliography entry to the correct scholarly work and publication version when evidence permits, then acquire only lawful, policy-approved source material with explicit access and license provenance.

**Architecture:** Provider adapters return normalized candidate records behind stable protocols. A deterministic matcher performs identity selection before any model fallback. The acquisition service separates location discovery, URL security, license/access policy and byte registration so a metadata hit can never silently become a full-text claim.

**Tech Stack:** Python 3.13, FastAPI, httpx, PostgreSQL, Crossref REST API, OpenAlex API, Semantic Scholar Academic Graph API, Unpaywall API, S3-compatible object storage, pytest, respx.

**Spec:** `docs/superpowers/specs/2026-08-28-citetrace-product-system-design.md`, `docs/02_COMPETITIVE_STRATEGY.md`, `docs/03_DOMAIN_TAXONOMY.md`, `docs/04_SYSTEM_ARCHITECTURE.md`, `docs/05_AGENT_AI_PIPELINE.md`, `docs/06_DATA_MODEL_PROVENANCE.md`, `docs/10_SECURITY_PRIVACY_COPYRIGHT.md`, `config/source-policy.example.yaml`

## Global Constraints

- Never invent or repair a DOI, arXiv ID, PMID, title, author or year.
- Preserve every provider candidate and its response provenance, not only the selected result.
- Distinguish intellectual work identity from exact manifestation/version identity.
- A confirmed identifier conflict is a hard conflict and cannot be overridden by title similarity.
- Provider metadata is corroborating evidence, never an unquestioned source of truth.
- Do not bypass a paywall, authentication control, robots restriction or repository access rule.
- Every remote URL passes DNS/IP/redirect/content checks before bytes are fetched.
- Access level and exact asset version are user-visible and stored with every source span.
- Abstract-only and metadata-only records cannot produce full-text evidence claims.
- Provider costs, quotas and retry state remain outside domain judgment logic.

---

## File Structure

- `starter/services/api/src/citetrace_api/providers/` — provider protocols, clients and normalized DTOs.
- `starter/services/api/src/citetrace_api/resolution/` — bibliographic normalization, scoring and selection.
- `starter/services/api/src/citetrace_api/acquisition/` — OA discovery, URL safety, policy and fetch registration.
- `starter/services/api/src/citetrace_api/db/repositories/references.py` — candidates, works, versions and decisions.
- `starter/services/api/src/citetrace_api/db/repositories/source_assets.py` — acquired source persistence.
- `starter/services/api/tests/fixtures/provider/` — stable provider responses.

### Task 1: Provider-neutral scholarly metadata contracts

**Files:**
- Create: `starter/services/api/src/citetrace_api/providers/__init__.py`
- Create: `starter/services/api/src/citetrace_api/providers/models.py`
- Create: `starter/services/api/src/citetrace_api/providers/protocols.py`
- Create: `starter/services/api/src/citetrace_api/providers/http.py`
- Create: `starter/services/api/tests/test_provider_models.py`
- Create: `starter/services/api/tests/test_provider_http.py`
- Modify: `starter/services/api/src/citetrace_api/config.py`

**Interfaces:**
- Consumes: parsed `ReferenceEntryRecord` and provider configuration.
- Produces: `BibliographicQuery`, `ProviderCandidate`, `OpenAccessLocation`, `ProviderPage`, and shared bounded HTTP behavior.

- [ ] **Step 1: Write failing normalized candidate tests**

```python
from citetrace_api.providers.models import ProviderCandidate


def test_candidate_normalizes_doi_and_preserves_raw_snapshot() -> None:
    candidate = ProviderCandidate.from_provider(
        provider="crossref",
        provider_record_id="10.1000/ABC",
        title="  A   Foundation Method ",
        authors=["Smith, Jane", "Lee, Min"],
        year=2024,
        identifiers={"doi": "https://doi.org/10.1000/ABC"},
        raw_snapshot={"DOI": "10.1000/ABC"},
    )
    assert candidate.normalized_title == "a foundation method"
    assert candidate.identifiers["doi"] == "10.1000/abc"
    assert candidate.raw_snapshot["DOI"] == "10.1000/ABC"
```

Add tests for arXiv version suffixes, Unicode author names, missing year, multiple venues and malformed identifiers that remain absent rather than guessed.

- [ ] **Step 2: Define provider DTOs and protocols**

```python
@dataclass(frozen=True, slots=True)
class BibliographicQuery:
    reference_entry_id: UUID
    title: str | None
    authors: tuple[str, ...]
    year: int | None
    venue: str | None
    identifiers: Mapping[str, str]
    raw_reference: str


@dataclass(frozen=True, slots=True)
class ProviderCandidate:
    provider: str
    provider_record_id: str
    title: str
    normalized_title: str
    authors: tuple[str, ...]
    year: int | None
    venue: str | None
    identifiers: Mapping[str, str]
    version_hints: Mapping[str, str]
    access_hints: Mapping[str, object]
    raw_snapshot: Mapping[str, object]


class ScholarlyMetadataProvider(Protocol):
    name: str
    async def search(self, query: BibliographicQuery, trace_id: str) -> list[ProviderCandidate]: ...
```

- [ ] **Step 3: Write failing shared HTTP behavior tests**

Assert that the HTTP adapter:

- sends the configured user agent and contact email where required,
- enforces connect/read/total timeouts,
- respects `Retry-After` and provider rate headers,
- retries 429 and transient 5xx within a bounded attempt count,
- does not retry validation 4xx responses,
- records status, latency, response hash and safe headers,
- does not log API keys or full response bodies.

- [ ] **Step 4: Implement `ProviderHttpClient`**

```python
class ProviderHttpClient:
    async def get_json(
        self,
        *,
        provider: str,
        url: str,
        params: Mapping[str, str | int],
        headers: Mapping[str, str],
        trace_id: str,
        maximum_bytes: int,
    ) -> ProviderJsonResponse: ...
```

Use an injected clock and sleeper in tests. Limit decompressed response bytes, validate JSON media type and return a response-provenance record even on a classified failure.

- [ ] **Step 5: Add provider settings**

Add base URLs, API keys, contact email, per-provider concurrency, timeout and cache TTL settings. Secrets use `SecretStr`; their string representation must remain redacted.

- [ ] **Step 6: Run model and HTTP tests**

Run:

```bash
cd starter/services/api
pytest tests/test_provider_models.py tests/test_provider_http.py -v
pytest -q
```

Expected: normalization, retry and redaction tests pass.

- [ ] **Step 7: Commit provider contracts**

```bash
git add starter/services/api/src/citetrace_api/providers \
  starter/services/api/src/citetrace_api/config.py \
  starter/services/api/tests/test_provider_models.py starter/services/api/tests/test_provider_http.py
git commit -m "feat: define scholarly provider contracts"
```

### Task 2: Crossref, OpenAlex and Semantic Scholar adapters

**Files:**
- Create: `starter/services/api/src/citetrace_api/providers/crossref.py`
- Create: `starter/services/api/src/citetrace_api/providers/openalex.py`
- Create: `starter/services/api/src/citetrace_api/providers/semantic_scholar.py`
- Create: `starter/services/api/tests/fixtures/provider/crossref-title.json`
- Create: `starter/services/api/tests/fixtures/provider/openalex-work.json`
- Create: `starter/services/api/tests/fixtures/provider/semantic-scholar-paper.json`
- Create: `starter/services/api/tests/test_crossref_provider.py`
- Create: `starter/services/api/tests/test_openalex_provider.py`
- Create: `starter/services/api/tests/test_semantic_scholar_provider.py`

**Interfaces:**
- Consumes: `BibliographicQuery` and shared HTTP client.
- Produces: normalized provider candidates with exact provider IDs and response provenance.

- [ ] **Step 1: Write failing identifier-first adapter tests**

```python
@pytest.mark.anyio
async def test_crossref_uses_exact_doi_before_title_search(crossref: CrossrefProvider) -> None:
    query = BibliographicQuery(
        reference_entry_id=uuid4(),
        title="Foundation Method",
        authors=("Jane Smith",),
        year=2024,
        venue=None,
        identifiers={"doi": "10.1000/foundation"},
        raw_reference="Smith ...",
    )
    candidates = await crossref.search(query, trace_id="trace-1")
    assert candidates[0].identifiers["doi"] == "10.1000/foundation"
    assert exact_doi_route.called
    assert title_search_route.called is False
```

Create equivalent exact-ID tests for OpenAlex IDs, arXiv IDs and Semantic Scholar paper IDs where available.

- [ ] **Step 2: Implement Crossref adapter**

Use DOI endpoint for a normalized DOI, otherwise query works with title, first author and year. Parse title arrays, author family/given names, issued year, container title, subtype, relation/update metadata and resource links. Send the configured contact identity and retain Crossref response metadata.

- [ ] **Step 3: Implement OpenAlex adapter**

Use exact DOI or OpenAlex ID filters before broad search. Parse work ID, primary location, publication year/date, authorships, sources, type, DOI, PMID, PMCID, arXiv where present, referenced works, related versions and OA fields. Do not treat an OA URL as safe until the acquisition subsystem validates it.

- [ ] **Step 4: Implement Semantic Scholar adapter**

Use paper lookup for exact IDs and paper search for title fallback. Request only fields needed for identity and graph corroboration. Parse external IDs, title, authors, year, venue, publication types and open-access PDF metadata as hints.

- [ ] **Step 5: Add malformed and quota response tests**

For each provider, test missing fields, duplicate authors, unknown work type, partial results, 429, 5xx and invalid JSON. A provider failure returns a classified provider outcome while allowing other providers to continue.

- [ ] **Step 6: Run provider adapter tests**

Run:

```bash
cd starter/services/api
pytest tests/test_crossref_provider.py tests/test_openalex_provider.py \
  tests/test_semantic_scholar_provider.py -v
pytest -q
```

Expected: exact identifier lookup, normalized fallback search and failure isolation pass.

- [ ] **Step 7: Commit metadata adapters**

```bash
git add starter/services/api/src/citetrace_api/providers \
  starter/services/api/tests/fixtures/provider \
  starter/services/api/tests/test_crossref_provider.py \
  starter/services/api/tests/test_openalex_provider.py \
  starter/services/api/tests/test_semantic_scholar_provider.py
git commit -m "feat: add corroborating metadata providers"
```

### Task 3: Deterministic bibliographic matcher and ambiguity policy

**Files:**
- Create: `starter/services/api/src/citetrace_api/resolution/__init__.py`
- Create: `starter/services/api/src/citetrace_api/resolution/features.py`
- Create: `starter/services/api/src/citetrace_api/resolution/scoring.py`
- Create: `starter/services/api/src/citetrace_api/resolution/decision.py`
- Create: `starter/services/api/src/citetrace_api/resolution/service.py`
- Create: `starter/services/api/tests/test_resolution_features.py`
- Create: `starter/services/api/tests/test_resolution_decision.py`
- Create: `starter/services/api/tests/test_resolution_service.py`
- Create: `config/reference-resolution.example.yaml`

**Interfaces:**
- Consumes: one reference entry and all normalized provider candidates.
- Produces: retained candidate feature rows and one `ResolutionDecision` with status, score, margin, reason codes and selected work/version or abstention.

- [ ] **Step 1: Write failing feature tests**

```python
def test_confirmed_doi_conflict_is_hard_conflict() -> None:
    features = compare_reference_to_candidate(
        reference=reference(doi="10.1000/a", title="Same title"),
        candidate=candidate(doi="10.1000/b", title="Same title"),
    )
    assert "doi_conflict" in features.hard_conflicts
    assert features.identifier_score == 0.0
```

Add cases for exact DOI, arXiv version mismatch, normalized title tokens, author overlap, year distance, venue similarity, retraction/correction notices and conference-to-journal expansion hints.

- [ ] **Step 2: Define the scored feature vector**

```python
@dataclass(frozen=True, slots=True)
class ResolutionFeatures:
    identifier_score: float
    title_score: float
    author_score: float
    year_score: float
    venue_score: float
    version_score: float
    provider_agreement_score: float
    hard_conflicts: tuple[str, ...]


def weighted_score(features: ResolutionFeatures, weights: ResolutionWeights) -> float: ...
```

Hard conflicts force rejection. Missing values redistribute no weight; they reduce evidence coverage and affect confidence separately.

- [ ] **Step 3: Add an explicit threshold profile**

Create `config/reference-resolution.example.yaml`:

```yaml
version: 1.0.0
profiles:
  default:
    accept_score: 0.92
    minimum_margin: 0.08
    version_uncertainty_accept_score: 0.95
    ambiguous_floor: 0.80
    weights:
      identifier: 0.35
      title: 0.25
      authors: 0.15
      year: 0.08
      venue: 0.05
      version: 0.07
      provider_agreement: 0.05
```

- [ ] **Step 4: Write failing decision-table tests**

Test these outcomes:

- exact DOI and compatible metadata → `resolved`;
- same work, unclear preprint/publisher manifestation → `resolved_with_version_uncertainty`;
- two candidates above floor with margin below threshold → `ambiguous`;
- no candidate above floor → `unresolved`;
- dataset/software/web citation classified from reference structure → `not_a_scholarly_work` only when no scholarly work match is expected;
- exact identifier conflict → candidate rejected even with title score 1.0.

- [ ] **Step 5: Implement pure decision logic**

```python
@dataclass(frozen=True, slots=True)
class ResolutionDecision:
    status: ResolutionStatus
    selected_candidate_id: UUID | None
    absolute_score: float | None
    score_margin: float | None
    reason_codes: tuple[str, ...]
    requires_human_review: bool
```

Keep the decision function deterministic and free of database/network calls.

- [ ] **Step 6: Write failing multi-provider service tests**

Assert that the service queries available providers concurrently within per-provider limits, stores every candidate and failed provider outcome, deduplicates candidates by normalized external IDs, computes provider agreement and persists one current decision.

- [ ] **Step 7: Implement `ReferenceResolutionService`**

```python
class ReferenceResolutionService:
    async def resolve(self, reference_entry_id: UUID, trace_id: str) -> ResolutionDecision: ...
```

Use deterministic matching first. Invoke the versioned prompt `reference_resolution_fallback` only when candidates are close and no hard conflict exists. Validate the model output against its schema, and never permit it to introduce a candidate ID absent from input.

- [ ] **Step 8: Run resolution tests and sample calibration**

Run:

```bash
cd starter/services/api
pytest tests/test_resolution_features.py tests/test_resolution_decision.py \
  tests/test_resolution_service.py -v
pytest -q
```

Expected: all decision-table and provider-isolation tests pass.

- [ ] **Step 9: Commit the deterministic resolver**

```bash
git add config/reference-resolution.example.yaml \
  starter/services/api/src/citetrace_api/resolution \
  starter/services/api/tests/test_resolution_features.py \
  starter/services/api/tests/test_resolution_decision.py \
  starter/services/api/tests/test_resolution_service.py
git commit -m "feat: resolve references with explicit ambiguity"
```

### Task 4: Work/version identity persistence and user confirmation

**Files:**
- Create: `starter/services/api/src/citetrace_api/db/repositories/references.py`
- Create: `starter/services/api/src/citetrace_api/routes/references.py`
- Create: `starter/services/api/tests/test_reference_repository.py`
- Create: `starter/services/api/tests/test_reference_confirmation_api.py`
- Modify: `contracts/openapi.yaml`
- Modify: `contracts/event_catalog.yaml`
- Modify: `starter/services/api/src/citetrace_api/main.py`

**Interfaces:**
- Consumes: provider candidates and `ResolutionDecision`.
- Produces: canonical `scholarly_work`, exact `work_version`, append-only `reference_resolution`, and user-confirmation API/event.

- [ ] **Step 1: Write failing identity merge tests**

Assert that:

- the same normalized DOI maps to one work version;
- arXiv v1 and v2 are distinct manifestations under one work;
- a conference paper and journal expansion remain distinct versions unless provider relations and metadata justify one work lineage;
- a correction or retraction notice is stored as its own version and linked by status notice;
- no merge occurs on title alone when authors materially differ.

- [ ] **Step 2: Implement focused repository operations**

```python
class ReferenceRepository:
    async def add_candidates(self, reference_entry_id: UUID, candidates: Sequence[ScoredCandidate]) -> None: ...
    async def upsert_work_identity(self, identity: WorkIdentity) -> WorkVersionIdentity: ...
    async def append_resolution(self, decision: PersistedResolutionDecision) -> UUID: ...
    async def current_resolution(self, reference_entry_id: UUID) -> ResolutionRecord | None: ...
```

Use advisory locks keyed by normalized DOI/arXiv/PMID when creating canonical identities to avoid duplicate concurrent rows.

- [ ] **Step 3: Write failing confirmation endpoint tests**

```python
def test_user_can_confirm_one_existing_candidate(client: TestClient, ambiguous_reference: UUID) -> None:
    response = client.post(
        f"/v1/references/{ambiguous_reference}:confirm-resolution",
        headers={"Idempotency-Key": "confirm-reference-001"},
        json={"candidate_id": str(CANDIDATE_ID)},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "user_confirmed"
```

Reject candidate IDs not belonging to the reference, cross-workspace access and confirmation of deleted source records.

- [ ] **Step 4: Implement append-only confirmation**

Never update the prior decision fields in place. Pre-generate the new decision UUID, set the old current decision's `superseded_by_id`, insert the new `user_confirmed` decision and emit `reference.resolution.confirmed` in one transaction.

- [ ] **Step 5: Update OpenAPI and event contracts**

Document candidate listing, ambiguity reason codes, exact version uncertainty and confirmation semantics. A user-confirmed identity is visible as such in provenance and can be re-adjudicated without deleting history.

- [ ] **Step 6: Run identity and API tests**

Run:

```bash
python scripts/validate_package.py
cd starter/services/api
pytest tests/test_reference_repository.py tests/test_reference_confirmation_api.py -v
pytest -q
```

Expected: identity uniqueness, append-only history and tenant authorization pass.

- [ ] **Step 7: Commit reference identity persistence**

```bash
git add contracts/openapi.yaml contracts/event_catalog.yaml \
  starter/services/api/src/citetrace_api/db/repositories/references.py \
  starter/services/api/src/citetrace_api/routes/references.py \
  starter/services/api/src/citetrace_api/main.py \
  starter/services/api/tests/test_reference_repository.py \
  starter/services/api/tests/test_reference_confirmation_api.py
git commit -m "feat: persist work versions and resolution history"
```

### Task 5: SSRF-resistant URL validation and redirect policy

**Files:**
- Create: `starter/services/api/src/citetrace_api/acquisition/__init__.py`
- Create: `starter/services/api/src/citetrace_api/acquisition/url_guard.py`
- Create: `starter/services/api/src/citetrace_api/acquisition/fetcher.py`
- Create: `starter/services/api/tests/test_url_guard.py`
- Create: `starter/services/api/tests/test_safe_fetcher.py`

**Interfaces:**
- Consumes: provider-supplied candidate URL and source-policy profile.
- Produces: `ValidatedRemoteLocation` or stable denial code; fetched bytes only after every redirect is revalidated.

- [ ] **Step 1: Write failing URL guard tests**

Test denial of:

- `http://` when HTTPS is required,
- localhost, loopback, link-local and RFC1918 addresses,
- IPv6 loopback and unique-local ranges,
- credentials embedded in URLs,
- non-443 ports,
- DNS answers containing a denied address,
- redirect from a public host to a private address,
- DNS rebinding between validation and connection.

Test acceptance of a public HTTPS host with a stable public address.

- [ ] **Step 2: Define explicit denial codes**

```python
class UrlDenialCode(StrEnum):
    SCHEME_NOT_ALLOWED = "scheme_not_allowed"
    CREDENTIALS_NOT_ALLOWED = "credentials_not_allowed"
    PORT_NOT_ALLOWED = "port_not_allowed"
    HOST_NOT_ALLOWED = "host_not_allowed"
    PRIVATE_ADDRESS = "private_address"
    DNS_RESOLUTION_FAILED = "dns_resolution_failed"
    REDIRECT_LIMIT_EXCEEDED = "redirect_limit_exceeded"
    DNS_REBINDING_DETECTED = "dns_rebinding_detected"
```

- [ ] **Step 3: Implement DNS and IP validation**

```python
class UrlGuard:
    async def validate(self, url: str) -> ValidatedRemoteLocation: ...
```

Resolve all A/AAAA records, reject when any answer is non-global, retain the approved addresses and hostname, and require the fetcher to connect using a transport that verifies the peer against the approved set while preserving TLS hostname verification.

- [ ] **Step 4: Write failing redirect and content tests**

Assert that the fetcher re-runs URL validation for every redirect, accepts only configured media types, limits decompressed bytes, checks PDF magic for PDF claims, records final URL and response headers, and aborts on content-type mismatch.

- [ ] **Step 5: Implement `SafeRemoteFetcher`**

```python
class SafeRemoteFetcher:
    async def fetch(
        self,
        location: ValidatedRemoteLocation,
        *,
        maximum_bytes: int,
        allowed_media_types: frozenset[str],
        trace_id: str,
    ) -> FetchedRemoteAsset: ...
```

Do not follow redirects automatically in httpx. Process each response manually and cap redirects at the policy value.

- [ ] **Step 6: Run URL security tests**

Run:

```bash
cd starter/services/api
pytest tests/test_url_guard.py tests/test_safe_fetcher.py -v
pytest -q
```

Expected: all private-network, redirect and content-confusion cases are blocked.

- [ ] **Step 7: Commit URL security boundary**

```bash
git add starter/services/api/src/citetrace_api/acquisition \
  starter/services/api/tests/test_url_guard.py starter/services/api/tests/test_safe_fetcher.py
git commit -m "feat: enforce SSRF-resistant source fetching"
```

### Task 6: Unpaywall and lawful repository acquisition pipeline

**Files:**
- Create: `starter/services/api/src/citetrace_api/providers/unpaywall.py`
- Create: `starter/services/api/src/citetrace_api/acquisition/policy.py`
- Create: `starter/services/api/src/citetrace_api/acquisition/service.py`
- Create: `starter/services/api/src/citetrace_api/db/repositories/source_assets.py`
- Create: `starter/services/api/tests/fixtures/provider/unpaywall-oa.json`
- Create: `starter/services/api/tests/test_unpaywall_provider.py`
- Create: `starter/services/api/tests/test_acquisition_policy.py`
- Create: `starter/services/api/tests/test_source_acquisition_service.py`

**Interfaces:**
- Consumes: resolved work version, metadata/OA hints and source-policy profile.
- Produces: immutable full-text/abstract/metadata source asset, explicit `AccessLevel`, license/access provenance or `not_accessible` limitation.

- [ ] **Step 1: Write failing Unpaywall location tests**

Assert that the adapter normalizes DOI lookup, returns all candidate OA locations with host type, version, license and URL fields, and never labels a location lawful solely because a URL exists.

- [ ] **Step 2: Implement policy decision objects**

```python
@dataclass(frozen=True, slots=True)
class AcquisitionPolicyRequest:
    workspace_id: UUID
    work_version_id: UUID
    proposed_method: str
    proposed_url: str | None
    provider_access_metadata: Mapping[str, object]
    intended_storage_days: int


@dataclass(frozen=True, slots=True)
class AcquisitionPolicyDecision:
    allowed: bool
    access_level: AccessLevel
    reason_codes: tuple[str, ...]
    display_rule: str
    retention_days: int
```

A policy decision is required before network fetch, storage, model transmission and user sharing.

- [ ] **Step 3: Write a policy decision table test**

Cover:

- user-uploaded PDF → `user_private_full_text`;
- verified OA publisher PDF → `publisher_open_full_text`;
- accepted manuscript in institutional repository → `repository_manuscript`;
- provider abstract only → `abstract_only`;
- bibliographic fields only → `metadata_only`;
- subscription page or access-uncertain URL → `not_accessible` and no fetch.

- [ ] **Step 4: Implement ordered lawful acquisition**

```python
class SourceAcquisitionService:
    async def acquire(self, work_version_id: UUID, workspace_id: UUID, trace_id: str) -> AcquisitionOutcome: ...
```

Order:

1. reuse a valid user-owned asset for the exact work version;
2. query Unpaywall and approved repository metadata;
3. policy-filter and URL-validate candidate locations;
4. fetch and validate the highest-priority lawful location;
5. register immutable bytes and access provenance;
6. fall back to abstract or metadata assets;
7. return `not_accessible` when no inspectable material exists.

- [ ] **Step 5: Preserve exact version and access provenance**

Persist acquisition method, provider, source/final URL, response hash, access timestamp, license fields, terms snapshot, security result and work-version association. Do not reuse an asset for a different work version without an explicit version-equivalence decision.

- [ ] **Step 6: Add failure and deletion tests**

Test checksum mismatch, HTML masquerading as PDF, revoked location, expired retention, user deletion and fallback from one denied location to another approved location. Ensure logs contain no paper bytes or signed query tokens.

- [ ] **Step 7: Run acquisition tests**

Run:

```bash
cd starter/services/api
pytest tests/test_unpaywall_provider.py tests/test_acquisition_policy.py \
  tests/test_source_acquisition_service.py -v
pytest -q
```

Expected: no disallowed URL is fetched and every outcome has an explicit access level.

- [ ] **Step 8: Commit lawful acquisition**

```bash
git add starter/services/api/src/citetrace_api/providers/unpaywall.py \
  starter/services/api/src/citetrace_api/acquisition \
  starter/services/api/src/citetrace_api/db/repositories/source_assets.py \
  starter/services/api/tests/fixtures/provider/unpaywall-oa.json \
  starter/services/api/tests/test_unpaywall_provider.py \
  starter/services/api/tests/test_acquisition_policy.py \
  starter/services/api/tests/test_source_acquisition_service.py
git commit -m "feat: acquire lawful source versions with provenance"
```

### Task 7: Resolution/acquisition worker slice and user-visible limitations

**Files:**
- Create: `starter/services/api/src/citetrace_api/orchestration/reference_handlers.py`
- Create: `starter/services/api/tests/test_reference_pipeline.py`
- Modify: `starter/services/api/src/citetrace_api/orchestration/handlers.py`
- Modify: `starter/services/api/src/citetrace_api/routes/analyses.py`
- Modify: `contracts/event_catalog.yaml`
- Modify: `contracts/openapi.yaml`

**Interfaces:**
- Consumes: `document.parsed` and analysis scope.
- Produces: per-reference resolution/acquisition outcomes, stage progress, successor `analysis.references.ready` event and structured limitations.

- [ ] **Step 1: Write a failing pipeline integration test**

```python
@pytest.mark.anyio
async def test_parsed_document_resolves_and_acquires_each_in_scope_reference(pipeline: ReferencePipeline) -> None:
    result = await pipeline.run(analysis_id=ANALYSIS_ID, trace_id="trace-ref-1")
    assert result.total_references == 3
    assert result.resolved == 2
    assert result.ambiguous == 1
    assert result.full_text_available == 1
    assert result.abstract_only == 1
    assert result.not_accessible == 1
```

Assert that one failed provider does not fail the whole analysis and that progress units equal the number of in-scope reference entries.

- [ ] **Step 2: Implement bounded per-reference orchestration**

Use a workspace-configured concurrency semaphore. Each reference gets a durable stage attempt and retry budget. Emit progress after a transaction commits; never derive final status only from transient queue state.

- [ ] **Step 3: Map outcomes to structured limitations**

Stable codes include:

- `reference_ambiguous`,
- `reference_unresolved`,
- `source_not_accessible`,
- `source_abstract_only`,
- `version_uncertain`,
- `provider_temporarily_unavailable`,
- `source_security_rejected`.

Each limitation includes user-safe text and an actionable recovery such as upload source, confirm candidate or retry provider.

- [ ] **Step 4: Update API/event contracts**

Add reference progress counts, resolution summary and access summary. Limited outcomes remain successful domain outcomes and do not become a generic HTTP 500.

- [ ] **Step 5: Run integration and contract tests**

Run:

```bash
python scripts/validate_package.py
cd starter/services/api
pytest tests/test_reference_pipeline.py -v
pytest -q
```

Expected: mixed reference outcomes complete the stage deterministically.

- [ ] **Step 6: Commit the reference/source vertical slice**

```bash
git add contracts/openapi.yaml contracts/event_catalog.yaml \
  starter/services/api/src/citetrace_api/orchestration/reference_handlers.py \
  starter/services/api/src/citetrace_api/orchestration/handlers.py \
  starter/services/api/src/citetrace_api/routes/analyses.py \
  starter/services/api/tests/test_reference_pipeline.py
git commit -m "feat: complete reference and source acquisition slice"
```

## Plan Acceptance Gate

Run:

```bash
cd starter/services/api
pytest -q
ruff check src tests
mypy src
cd ../../..
python scripts/validate_package.py
```

Accept the plan only when:

- every bibliography entry has a retained candidate history and one explicit current resolution status;
- exact identifier conflicts cannot be selected;
- version uncertainty is visible and not collapsed into certainty;
- provider outages degrade individual references without corrupting the analysis;
- no private, loopback, link-local or disallowed redirect target can be fetched;
- no subscription-only page is treated as available full text;
- every acquired asset has exact version, access, license, URL, checksum and acquisition provenance;
- inaccessible and abstract-only references produce correct limitations and never fabricated quotes;
- tenant, contract, unit and integration tests pass.
