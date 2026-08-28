# CiteTrace Foundation and Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the in-memory foundation with a tenant-isolated, immutable PDF ingestion pipeline that stores exact source bytes, invokes GROBID safely, and persists normalized document structure, references and citation anchors.

**Architecture:** Keep the modular-monolith API, PostgreSQL repositories and an outbox-driven worker boundary. Source bytes are immutable objects; parsed artifacts are append-only versions. Every tenant transaction uses `SET LOCAL app.workspace_id`, and GROBID output is normalized without using GROBID consolidation.

**Tech Stack:** Python 3.13, FastAPI 0.141.1, SQLAlchemy async, psycopg 3, PostgreSQL 18 + pgvector, S3-compatible object storage, httpx, defusedxml/lxml, pypdf, pytest.

**Spec:** `docs/superpowers/specs/2026-08-28-citetrace-product-system-design.md`, `docs/00_MASTER_BLUEPRINT.md`, `docs/04_SYSTEM_ARCHITECTURE.md`, `docs/06_DATA_MODEL_PROVENANCE.md`, `docs/10_SECURITY_PRIVACY_COPYRIGHT.md`, `contracts/db/schema.sql`, `contracts/event_catalog.yaml`

## Global Constraints

- Accept only born-digital scientific PDFs in the initial release; scanned or image-only documents produce a structured limitation.
- Enforce 1–60 pages, no more than 150 bibliography entries and no more than 100 MiB per uploaded file.
- Never mutate source bytes or parsed-document versions after creation.
- Use `SET LOCAL app.workspace_id`, never session-level `SET`, inside every tenant transaction.
- Disable GROBID header and citation consolidation; reference identity belongs to the dedicated resolution subsystem.
- Treat PDF text, metadata, XML and filenames as untrusted input.
- Every external request has an explicit timeout, bounded retry policy and trace ID.
- Preserve exact normalized offsets, page numbers and bounding boxes when available; mark coordinate gaps rather than inventing them.
- Follow TDD and commit after every task passes its focused and regression tests.

---

## File Structure

- `starter/services/api/src/citetrace_api/db/session.py` — async engine, tenant transaction and health checks.
- `starter/services/api/src/citetrace_api/db/repositories/` — focused persistence adapters.
- `starter/services/api/src/citetrace_api/documents/` — upload validation, object storage and document registry.
- `starter/services/api/src/citetrace_api/parsing/` — GROBID client, TEI parser and normalizer.
- `starter/services/api/src/citetrace_api/orchestration/` — outbox events and stage state.
- `starter/services/api/src/citetrace_api/routes/documents.py` — upload and document status endpoints.
- `starter/services/api/migrations/0001_initial.sql` — deployed copy of the canonical database contract.
- `starter/services/api/tests/fixtures/` — deterministic PDF and TEI fixtures.

### Task 1: Async database session and tenant transaction boundary

**Files:**
- Create: `starter/services/api/src/citetrace_api/db/__init__.py`
- Create: `starter/services/api/src/citetrace_api/db/session.py`
- Create: `starter/services/api/src/citetrace_api/db/repositories/analysis.py`
- Create: `starter/services/api/tests/test_tenant_session.py`
- Create: `starter/services/api/tests/test_analysis_repository.py`
- Modify: `starter/services/api/pyproject.toml`
- Modify: `starter/services/api/src/citetrace_api/config.py`
- Create: `starter/services/api/migrations/0001_initial.sql`

**Interfaces:**
- Consumes: `AnalysisCreateRequest`, `Analysis`, and `contracts/db/schema.sql`.
- Produces: `Database`, `tenant_transaction(workspace_id)`, and `AnalysisRepository.create/get/cancel` for API and worker tasks.

- [ ] **Step 1: Write the failing tenant-boundary test**

```python
from uuid import uuid4

import pytest
from sqlalchemy import text

from citetrace_api.db.session import Database


@pytest.mark.anyio
async def test_tenant_transaction_sets_local_workspace(database: Database) -> None:
    workspace_id = uuid4()
    async with database.tenant_transaction(workspace_id) as session:
        observed = await session.scalar(text("select current_setting('app.workspace_id', true)"))
        assert observed == str(workspace_id)
```

- [ ] **Step 2: Add database dependencies and settings**

Add these dependencies to `starter/services/api/pyproject.toml`:

```toml
"psycopg[binary,pool]>=3.2,<4",
"sqlalchemy[asyncio]>=2.0,<3",
```

Add to `Settings`:

```python
database_url: str = "postgresql+psycopg://citetrace:citetrace@localhost:5432/citetrace"
database_pool_size: int = Field(default=10, ge=1, le=50)
database_pool_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
```

- [ ] **Step 3: Implement the async tenant transaction**

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


class Database:
    def __init__(self, url: str, pool_size: int, pool_timeout: float) -> None:
        self.engine: AsyncEngine = create_async_engine(
            url,
            pool_size=pool_size,
            pool_timeout=pool_timeout,
            pool_pre_ping=True,
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    @asynccontextmanager
    async def tenant_transaction(self, workspace_id: UUID) -> AsyncIterator[AsyncSession]:
        async with self.sessions() as session, session.begin():
            await session.execute(
                text("select set_config('app.workspace_id', :workspace_id, true)"),
                {"workspace_id": str(workspace_id)},
            )
            yield session
```

- [ ] **Step 4: Run the tenant test against the local PostgreSQL service**

Run:

```bash
docker compose -f starter/compose.yaml up -d postgres
cd starter/services/api
pytest tests/test_tenant_session.py -v
```

Expected: PASS, and the connection returned to the pool does not retain `app.workspace_id` outside the transaction.

- [ ] **Step 5: Write the failing persistent analysis repository tests**

```python
@pytest.mark.anyio
async def test_analysis_repository_replays_same_idempotent_request(
    database: Database,
    workspace_and_asset: tuple[UUID, UUID],
) -> None:
    workspace_id, asset_id = workspace_and_asset
    command = NewAnalysis(
        workspace_id=workspace_id,
        source_asset_id=asset_id,
        mode="understand",
        audience="beginner",
        requested_scope={"kind": "whole_document"},
        source_policy_profile="lawful-open-or-user-upload",
        pipeline_version="1.0.0",
        idempotency_key="analysis-create-001",
        input_fingerprint="a" * 64,
    )
    async with database.tenant_transaction(workspace_id) as session:
        first = await AnalysisRepository(session).create(command)
    async with database.tenant_transaction(workspace_id) as session:
        second = await AnalysisRepository(session).create(command)
    assert first.id == second.id
```

Also assert that reusing the same key with a different fingerprint raises `IdempotencyConflictError`, and a different workspace cannot read the row.

- [ ] **Step 6: Implement SQLAlchemy Core repository methods**

Use explicit Core statements against schema-qualified tables. The public signatures are:

```python
@dataclass(frozen=True, slots=True)
class NewAnalysis:
    workspace_id: UUID
    source_asset_id: UUID
    mode: str
    audience: str
    requested_scope: dict[str, object]
    source_policy_profile: str
    pipeline_version: str
    idempotency_key: str
    input_fingerprint: str


class AnalysisRepository:
    def __init__(self, session: AsyncSession) -> None: ...
    async def create(self, command: NewAnalysis) -> AnalysisRecord: ...
    async def get(self, analysis_id: UUID) -> AnalysisRecord | None: ...
    async def cancel(self, analysis_id: UUID) -> AnalysisRecord | None: ...
```

Use `INSERT ... ON CONFLICT (workspace_id, idempotency_key) DO NOTHING`, then read and compare the stored fingerprint before returning the durable record.

- [ ] **Step 7: Copy and verify the initial migration**

Run:

```bash
cp contracts/db/schema.sql starter/services/api/migrations/0001_initial.sql
cmp contracts/db/schema.sql starter/services/api/migrations/0001_initial.sql
python scripts/validate_package.py
```

Expected: both files are byte-identical and all contract checks pass.

- [ ] **Step 8: Run focused and full API tests**

Run:

```bash
cd starter/services/api
pytest tests/test_tenant_session.py tests/test_analysis_repository.py -v
pytest -q
```

Expected: all tests pass.

- [ ] **Step 9: Commit the database boundary**

```bash
git add starter/services/api/pyproject.toml starter/services/api/src/citetrace_api/config.py \
  starter/services/api/src/citetrace_api/db starter/services/api/tests/test_tenant_session.py \
  starter/services/api/tests/test_analysis_repository.py starter/services/api/migrations/0001_initial.sql
git commit -m "feat: add tenant-isolated database foundation"
```

### Task 2: Immutable object storage and secure PDF validation

**Files:**
- Create: `starter/services/api/src/citetrace_api/documents/models.py`
- Create: `starter/services/api/src/citetrace_api/documents/storage.py`
- Create: `starter/services/api/src/citetrace_api/documents/pdf_validation.py`
- Create: `starter/services/api/src/citetrace_api/documents/registry.py`
- Create: `starter/services/api/tests/test_pdf_validation.py`
- Create: `starter/services/api/tests/test_document_registry.py`
- Create: `starter/services/api/tests/fixtures/minimal-born-digital.pdf`
- Create: `starter/services/api/tests/fixtures/image-only.pdf`
- Modify: `starter/services/api/pyproject.toml`
- Modify: `starter/services/api/src/citetrace_api/config.py`

**Interfaces:**
- Consumes: authenticated workspace ID and an upload byte stream.
- Produces: immutable `RegisteredSourceAsset`, `ObjectStore`, `PdfValidationReport`, and source-asset rows for parsing.

- [ ] **Step 1: Write failing PDF validator tests**

```python
from pathlib import Path

from citetrace_api.documents.pdf_validation import PdfValidationCode, validate_pdf

FIXTURES = Path(__file__).parent / "fixtures"


def test_accepts_small_born_digital_pdf() -> None:
    report = validate_pdf((FIXTURES / "minimal-born-digital.pdf").read_bytes())
    assert report.accepted is True
    assert report.page_count == 1
    assert report.code == PdfValidationCode.ACCEPTED


def test_rejects_image_only_pdf_without_ocr() -> None:
    report = validate_pdf((FIXTURES / "image-only.pdf").read_bytes())
    assert report.accepted is False
    assert report.code == PdfValidationCode.IMAGE_ONLY_UNSUPPORTED
```

Add cases for invalid magic bytes, encrypted PDFs, more than 60 pages, 100 MiB limit and malformed cross-reference data.

- [ ] **Step 2: Add deterministic PDF and storage dependencies**

Add:

```toml
"boto3>=1.40,<2",
"pypdf>=6,<7",
"python-multipart>=0.0.20,<1",
```

Add settings for S3 endpoint, bucket, access key, secret key and `maximum_upload_bytes=104857600`.

- [ ] **Step 3: Implement bounded PDF validation**

```python
class PdfValidationCode(StrEnum):
    ACCEPTED = "accepted"
    INVALID_MAGIC = "invalid_magic"
    MALFORMED = "malformed_pdf"
    ENCRYPTED = "encrypted_pdf"
    PAGE_LIMIT_EXCEEDED = "page_limit_exceeded"
    BYTE_LIMIT_EXCEEDED = "byte_limit_exceeded"
    IMAGE_ONLY_UNSUPPORTED = "image_only_unsupported"


@dataclass(frozen=True, slots=True)
class PdfValidationReport:
    accepted: bool
    code: PdfValidationCode
    page_count: int | None
    extracted_character_count: int
```

Read through `pypdf.PdfReader` from memory, reject encrypted input, cap pages before extracting text, and classify image-only when total normalized text is below 40 characters across the document.

- [ ] **Step 4: Write the failing immutable object-store test**

```python
@pytest.mark.anyio
async def test_put_if_absent_never_overwrites_different_bytes(fake_store: FakeObjectStore) -> None:
    first = await fake_store.put_if_absent("workspace/a.pdf", b"first", "application/pdf")
    second = await fake_store.put_if_absent("workspace/a.pdf", b"second", "application/pdf")
    assert first.created is True
    assert second.created is False
    assert await fake_store.read("workspace/a.pdf") == b"first"
```

- [ ] **Step 5: Implement object storage protocol and S3 adapter**

```python
class ObjectStore(Protocol):
    async def put_if_absent(self, key: str, data: bytes, media_type: str) -> PutResult: ...
    async def read(self, key: str) -> bytes: ...
    async def delete(self, key: str) -> None: ...


def source_object_key(workspace_id: UUID, sha256_hex: str) -> str:
    return f"workspaces/{workspace_id}/source-assets/{sha256_hex[:2]}/{sha256_hex}.pdf"
```

Use conditional creation semantics. If the backend lacks a native create-only condition, write to a unique staging key, verify checksum, then use an atomic copy that fails when the destination exists.

- [ ] **Step 6: Write the failing registry transaction test**

Assert that the registry:

- hashes bytes before object-key selection,
- validates before storage,
- creates one source-asset row for repeated identical bytes,
- marks scan status `clean` only after validation,
- removes staged bytes when the database transaction fails.

- [ ] **Step 7: Implement `DocumentRegistry.register_upload`**

```python
@dataclass(frozen=True, slots=True)
class RegisterUpload:
    workspace_id: UUID
    original_filename: str
    media_type: str
    data: bytes
    retention_expires_at: datetime


class DocumentRegistry:
    async def register_upload(self, command: RegisterUpload) -> RegisteredSourceAsset: ...
```

Store only a sanitized display filename in metadata. Never use the user filename in an object key. Persist `acquisition_method=user_upload`, `access_level=user_private_full_text`, exact SHA-256, byte size and retention date.

- [ ] **Step 8: Run document tests**

Run:

```bash
cd starter/services/api
pytest tests/test_pdf_validation.py tests/test_document_registry.py -v
pytest -q
```

Expected: all upload validation and immutability cases pass.

- [ ] **Step 9: Commit secure source registration**

```bash
git add starter/services/api/pyproject.toml starter/services/api/src/citetrace_api/config.py \
  starter/services/api/src/citetrace_api/documents starter/services/api/tests/test_pdf_validation.py \
  starter/services/api/tests/test_document_registry.py starter/services/api/tests/fixtures
git commit -m "feat: register immutable validated PDF assets"
```

### Task 3: Document upload API and durable ingestion event

**Files:**
- Create: `starter/services/api/src/citetrace_api/routes/documents.py`
- Create: `starter/services/api/src/citetrace_api/orchestration/outbox.py`
- Create: `starter/services/api/src/citetrace_api/db/repositories/outbox.py`
- Create: `starter/services/api/tests/test_documents_api.py`
- Create: `starter/services/api/tests/test_outbox_repository.py`
- Modify: `starter/services/api/src/citetrace_api/main.py`
- Modify: `contracts/openapi.yaml`
- Modify: `contracts/event_catalog.yaml`

**Interfaces:**
- Consumes: multipart PDF, authenticated `ActorContext`, idempotency key and `DocumentRegistry`.
- Produces: `POST /v1/documents`, `GET /v1/documents/{source_asset_id}`, and `document.source.registered` outbox events.

- [ ] **Step 1: Add failing document endpoint tests**

```python
def test_upload_returns_201_and_source_asset(client: TestClient, pdf_bytes: bytes) -> None:
    response = client.post(
        "/v1/documents",
        headers={"Idempotency-Key": "upload-asset-001", "X-Workspace-Id": str(WORKSPACE_ID)},
        files={"file": ("paper.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["access_level"] == "user_private_full_text"
    assert body["security_scan_status"] == "clean"
    assert body["sha256"]
```

Add tests for unsupported content, duplicate idempotent upload and a workspace mismatch.

- [ ] **Step 2: Define the response and problem contracts**

Add `SourceAsset`, `PdfValidationProblem` and upload paths to `contracts/openapi.yaml`. The response includes `id`, `workspace_id`, `sha256`, `media_type`, `byte_size`, `access_level`, `security_scan_status`, `created_at` and links; it never includes object-store credentials or internal keys.

- [ ] **Step 3: Write the failing transactional outbox test**

```python
@pytest.mark.anyio
async def test_source_asset_and_event_commit_together(document_service: DocumentService) -> None:
    result = await document_service.register_upload(command)
    events = await outbox_repository.pending_for_aggregate(result.id)
    assert [event.event_type for event in events] == ["document.source.registered"]
    assert events[0].payload["source_asset_id"] == str(result.id)
```

- [ ] **Step 4: Implement the outbox record**

```python
@dataclass(frozen=True, slots=True)
class NewOutboxEvent:
    aggregate_type: str
    aggregate_id: UUID
    event_type: str
    schema_version: str
    workspace_id: UUID
    payload: dict[str, object]


class OutboxRepository:
    async def add(self, event: NewOutboxEvent) -> UUID: ...
    async def claim_batch(self, worker_id: str, limit: int) -> list[OutboxRecord]: ...
    async def mark_published(self, event_id: UUID) -> None: ...
```

Use `FOR UPDATE SKIP LOCKED` for claims and increment attempts atomically.

- [ ] **Step 5: Implement the upload route and service composition**

The route reads at most `maximum_upload_bytes + 1`, rejects larger streams before registry invocation and passes the actor's authorized workspace ID rather than trusting a form field.

- [ ] **Step 6: Register the router and exception mappings**

Map validation codes to stable RFC 9457-style problem codes. Image-only input returns 422 with recoverable action `upload_born_digital_pdf`; malware or invalid content returns 400 or 422 without parser details.

- [ ] **Step 7: Validate contracts and run endpoint tests**

Run:

```bash
python scripts/validate_package.py
cd starter/services/api
pytest tests/test_documents_api.py tests/test_outbox_repository.py -v
pytest -q
```

Expected: contract validation and all API tests pass.

- [ ] **Step 8: Commit the upload API**

```bash
git add contracts/openapi.yaml contracts/event_catalog.yaml \
  starter/services/api/src/citetrace_api/routes/documents.py \
  starter/services/api/src/citetrace_api/orchestration \
  starter/services/api/src/citetrace_api/db/repositories/outbox.py \
  starter/services/api/src/citetrace_api/main.py starter/services/api/tests/test_documents_api.py \
  starter/services/api/tests/test_outbox_repository.py
git commit -m "feat: expose durable document ingestion API"
```

### Task 4: GROBID client with bounded retries and raw TEI persistence

**Files:**
- Create: `starter/services/api/src/citetrace_api/parsing/grobid_client.py`
- Create: `starter/services/api/src/citetrace_api/parsing/models.py`
- Create: `starter/services/api/src/citetrace_api/parsing/service.py`
- Create: `starter/services/api/tests/test_grobid_client.py`
- Create: `starter/services/api/tests/test_parsing_service.py`
- Modify: `starter/services/api/pyproject.toml`
- Modify: `starter/services/api/src/citetrace_api/config.py`

**Interfaces:**
- Consumes: clean PDF bytes and immutable source-asset ID.
- Produces: `GrobidParseResult`, raw TEI object and one `parsed_document` version in `parsing` state.

- [ ] **Step 1: Write failing GROBID request tests**

Use `respx` to assert:

```python
@pytest.mark.anyio
async def test_fulltext_request_disables_consolidation(grobid_client: GrobidClient) -> None:
    result = await grobid_client.process_fulltext(b"%PDF fixture")
    request = grobid_route.calls.last.request
    assert request.url.params["consolidateHeader"] == "0"
    assert request.url.params["consolidateCitations"] == "0"
    assert request.url.params["teiCoordinates"] == "ref,biblStruct,p,head,figure,formula"
    assert result.tei_xml.startswith(b"<?xml")
```

Also test retry on 503 with `Retry-After`, no retry on 400, timeout classification and maximum response bytes.

- [ ] **Step 2: Add HTTP test/runtime dependencies and settings**

Add `httpx>=0.28,<1`, `respx>=0.22,<1` to development dependencies, plus:

```python
grobid_url: str = "http://localhost:8070"
grobid_connect_timeout_seconds: float = 5.0
grobid_read_timeout_seconds: float = 120.0
grobid_max_attempts: int = 3
grobid_max_response_bytes: int = 52428800
```

- [ ] **Step 3: Implement the GROBID client**

```python
class GrobidClient:
    async def process_fulltext(self, pdf_bytes: bytes, trace_id: str) -> GrobidParseResult: ...
```

POST to `/api/processFulltextDocument` as multipart data, set consolidation parameters to `0`, request the documented coordinate elements, stream the response with a byte limit and classify `503` as retryable. Use exponential delay capped at 10 seconds and honor a smaller valid `Retry-After` value.

- [ ] **Step 4: Write the failing raw-artifact persistence test**

Assert that `ParsingService.parse_source_asset`:

- reads the exact asset bytes,
- calls GROBID once for the input fingerprint,
- stores raw TEI at a content-addressed object key,
- creates a parsed-document row containing parser name/version/profile and raw artifact key,
- returns the existing parsed-document version on an identical retry.

- [ ] **Step 5: Implement parsing service idempotency**

Compute the input fingerprint from source SHA-256, parser name, parser version, profile and coordinate options. Use a unique database constraint to deduplicate retries and never overwrite a prior TEI artifact.

- [ ] **Step 6: Run parser client and service tests**

Run:

```bash
cd starter/services/api
pytest tests/test_grobid_client.py tests/test_parsing_service.py -v
pytest -q
```

Expected: retry, byte-limit, idempotency and persistence cases pass.

- [ ] **Step 7: Commit the isolated parser adapter**

```bash
git add starter/services/api/pyproject.toml starter/services/api/src/citetrace_api/config.py \
  starter/services/api/src/citetrace_api/parsing starter/services/api/tests/test_grobid_client.py \
  starter/services/api/tests/test_parsing_service.py
git commit -m "feat: add bounded GROBID parsing adapter"
```

### Task 5: TEI normalization, citation anchors and reference entries

**Files:**
- Create: `starter/services/api/src/citetrace_api/parsing/tei_reader.py`
- Create: `starter/services/api/src/citetrace_api/parsing/normalizer.py`
- Create: `starter/services/api/src/citetrace_api/parsing/quality.py`
- Create: `starter/services/api/src/citetrace_api/db/repositories/parsed_documents.py`
- Create: `starter/services/api/tests/fixtures/grobid-fulltext.tei.xml`
- Create: `starter/services/api/tests/test_tei_reader.py`
- Create: `starter/services/api/tests/test_document_normalizer.py`
- Create: `starter/services/api/tests/test_parse_quality.py`
- Modify: `starter/services/api/pyproject.toml`

**Interfaces:**
- Consumes: raw GROBID TEI plus exact source asset identity.
- Produces: `NormalizedDocument`, `ParsedNodeRecord`, `ReferenceEntryRecord`, `CitationClusterRecord`, `CitationAnchorRecord`, offset map and `ParseQualityReport`.

- [ ] **Step 1: Write failing fixture-based TEI extraction tests**

```python
def test_extracts_reference_and_links_in_text_anchor() -> None:
    document = read_tei(FIXTURE.read_bytes())
    assert document.references[0].local_label == "12"
    assert document.references[0].title == "Foundation Method"
    assert document.citation_clusters[0].anchor_text == "[12]"
    assert document.citation_clusters[0].target_reference_xml_ids == ["b12"]
```

Add fixtures for `[3–5]`, author-year clusters, missing target IDs, footnote citations and a bibliography item that is not a scholarly paper.

- [ ] **Step 2: Add safe XML dependencies**

Add:

```toml
"defusedxml>=0.7,<1",
"lxml>=6,<7",
```

Parse with entity resolution and network access disabled. Reject documents exceeding configured XML depth, node count or text size.

- [ ] **Step 3: Implement typed TEI reader output**

```python
@dataclass(frozen=True, slots=True)
class TeiReference:
    xml_id: str
    local_label: str
    raw_reference: str
    title: str | None
    authors: tuple[str, ...]
    year: int | None
    venue: str | None
    identifiers: dict[str, str]
    coordinates: tuple[BoundingBox, ...]


@dataclass(frozen=True, slots=True)
class TeiCitationCluster:
    anchor_text: str
    target_reference_xml_ids: tuple[str, ...]
    coordinates: tuple[BoundingBox, ...]
    context_node_xml_id: str
```

Do not assign canonical work IDs in this module.

- [ ] **Step 4: Write failing normalized-offset tests**

Assert that normalized text:

- has deterministic whitespace,
- preserves claim-significant punctuation and mathematical symbols,
- maps every citation cluster to exact start/end offsets,
- selects the same substring at those offsets,
- records `coordinate_missing` when a box is absent.

- [ ] **Step 5: Implement deterministic normalization and offset mapping**

```python
@dataclass(frozen=True, slots=True)
class OffsetMapping:
    normalized_start: int
    normalized_end: int
    tei_node_id: str
    page: int | None
    bounding_boxes: tuple[BoundingBox, ...]


class DocumentNormalizer:
    def normalize(self, tei: TeiDocument) -> NormalizedDocument: ...
```

Build text in structural order, normalize Unicode to NFC, collapse layout-only whitespace, retain sentence punctuation and compute SHA-256 for every persisted node.

- [ ] **Step 6: Write failing parse-quality grading tests**

Cases:

- Grade A: anchor/reference linkage ≥ 0.98, coordinate coverage ≥ 0.90 and meaningful body text.
- Grade B: linkage ≥ 0.90 and coordinate coverage ≥ 0.70.
- Grade C: usable text but material linkage/coordinate limitations.
- Grade D: no meaningful text, malformed hierarchy or bibliography extraction failure.

- [ ] **Step 7: Implement quality feature vector and repository write**

Persist nodes, references, clusters and anchors in one transaction. Grade D stops downstream automatic analysis and adds a structured limitation. Grade C permits reference browsing but marks every affected evidence link `review_required` until user confirmation.

- [ ] **Step 8: Run normalization regression tests**

Run:

```bash
cd starter/services/api
pytest tests/test_tei_reader.py tests/test_document_normalizer.py tests/test_parse_quality.py -v
pytest -q
```

Expected: all exact-offset, linkage and quality-grade assertions pass.

- [ ] **Step 9: Commit structural normalization**

```bash
git add starter/services/api/pyproject.toml starter/services/api/src/citetrace_api/parsing \
  starter/services/api/src/citetrace_api/db/repositories/parsed_documents.py \
  starter/services/api/tests/fixtures/grobid-fulltext.tei.xml \
  starter/services/api/tests/test_tei_reader.py starter/services/api/tests/test_document_normalizer.py \
  starter/services/api/tests/test_parse_quality.py
git commit -m "feat: normalize TEI citations with exact offsets"
```

### Task 6: Outbox worker and ingestion state machine

**Files:**
- Create: `starter/services/api/src/citetrace_api/orchestration/worker.py`
- Create: `starter/services/api/src/citetrace_api/orchestration/handlers.py`
- Create: `starter/services/api/src/citetrace_api/orchestration/stage_repository.py`
- Create: `starter/services/api/tests/test_ingestion_worker.py`
- Modify: `starter/services/api/src/citetrace_api/services/workflow.py`
- Modify: `starter/services/api/src/citetrace_api/main.py`
- Modify: `starter/compose.yaml`

**Interfaces:**
- Consumes: `document.source.registered` outbox event.
- Produces: parsing stage records, `document.parsed` or `document.parsing.limited` event, and a queryable document status.

- [ ] **Step 1: Write a failing end-to-end worker test**

```python
@pytest.mark.anyio
async def test_registered_document_reaches_parsed_state(
    worker: OutboxWorker,
    registered_document: RegisteredSourceAsset,
) -> None:
    await worker.run_once(limit=10)
    parsed = await parsed_repository.latest_for_asset(registered_document.id)
    assert parsed is not None
    assert parsed.parse_quality_grade in {"a", "b", "c"}
    assert await outbox_repository.has_event("document.parsed", registered_document.id)
```

Add cases for GROBID 503 exhaustion, Grade D, worker crash after database commit and event redelivery.

- [ ] **Step 2: Implement stage attempt records**

```python
class StageRepository:
    async def begin(self, analysis_run_id: UUID | None, stage_name: str, fingerprint: str) -> StageAttempt: ...
    async def succeed(self, attempt_id: UUID, output_artifact_ids: list[UUID]) -> None: ...
    async def limit(self, attempt_id: UUID, code: str, output_artifact_ids: list[UUID]) -> None: ...
    async def fail(self, attempt_id: UUID, code: str, safe_detail: str) -> None: ...
```

The same fingerprint returns the existing successful attempt instead of repeating side effects.

- [ ] **Step 3: Implement event handlers and bounded worker loop**

```python
class OutboxWorker:
    async def run_once(self, limit: int = 20) -> int: ...
```

Claim events with `SKIP LOCKED`, dispatch by exact event type and schema version, publish a successor event in the same transaction as the stage result, and mark the consumed event published afterward. Unknown schema versions are failed safely and alerted.

- [ ] **Step 4: Add worker process to local Compose**

Use the same API image with command:

```yaml
command: ["python", "-m", "citetrace_api.orchestration.worker"]
```

Give it no public port and the same database, Redis, GROBID and object-store configuration.

- [ ] **Step 5: Add document status projection**

Expose `GET /v1/documents/{source_asset_id}` with status values `registered`, `parsing`, `parsed`, `parsed_with_limits`, `failed`, `deleted`, latest parse-quality report and structured limitations.

- [ ] **Step 6: Run worker and regression tests**

Run:

```bash
cd starter/services/api
pytest tests/test_ingestion_worker.py -v
pytest -q
python ../../scripts/validate_package.py
```

Expected: redelivery is side-effect safe, every terminal failure has a stable code and all package checks pass.

- [ ] **Step 7: Commit the ingestion vertical slice**

```bash
git add starter/services/api/src/citetrace_api/orchestration \
  starter/services/api/src/citetrace_api/services/workflow.py \
  starter/services/api/src/citetrace_api/main.py starter/services/api/tests/test_ingestion_worker.py \
  starter/compose.yaml contracts/openapi.yaml contracts/event_catalog.yaml
git commit -m "feat: complete durable PDF ingestion slice"
```

## Plan Acceptance Gate

Run:

```bash
docker compose -f starter/compose.yaml up -d postgres redis grobid
cd starter/services/api
pytest -q
ruff check src tests
mypy src
cd ../../..
python scripts/validate_package.py
```

Accept the plan only when:

- a valid born-digital PDF creates immutable bytes, a parsed-document version, references and citation anchors;
- repeated events and API requests are idempotent;
- image-only, encrypted, malformed and oversized PDFs produce safe structured outcomes;
- a second workspace cannot read the first workspace's source asset or analysis records;
- exact citation anchor substrings match their stored normalized offsets;
- the raw GROBID TEI and normalized artifacts are versioned and traceable;
- no GROBID consolidation request is made;
- all tests, lint, type checks and package contract validation pass.
