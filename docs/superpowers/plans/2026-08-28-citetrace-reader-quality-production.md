# CiteTrace Reader, Quality and Production Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the inspectable three-pane reader, durable progress/feedback workflows, production security and observability, and release gates that prevent low-quality scientific judgments from reaching users.

**Architecture:** The Next.js reader consumes stable REST resources and replayable SSE events; it never renders raw model output. Public evidence views are read models assembled from audited database records. Feedback is append-only, evaluation is versioned, and operational telemetry uses artifact IDs and safe metadata rather than private paper content.

**Tech Stack:** Next.js 16.3.3, React 19.2.x, TypeScript, PDF.js, FastAPI, PostgreSQL, Server-Sent Events, OpenTelemetry, Prometheus-compatible metrics, Playwright, Vitest/Testing Library, pytest, k6 or Locust.

**Spec:** `docs/superpowers/specs/2026-08-28-citetrace-product-system-design.md`, `docs/01_PRODUCT_REQUIREMENTS_PRD.md`, `docs/07_API_EVENT_CONTRACTS.md`, `docs/08_UX_UI_SPEC.md`, `docs/09_EVALUATION_GOLDSET_QA.md`, `docs/10_SECURITY_PRIVACY_COPYRIGHT.md`, `docs/11_DEVOPS_SRE_COST.md`, `docs/14_GTM_METRICS.md`, `docs/18_ACCEPTANCE_CHECKLIST.md`

## Global Constraints

- The UI renders only audited evidence-link records and structured limitations, never unvalidated model prose.
- Every quote exposes source version, access level, section/page and exact-span status.
- Confidence is displayed stage by stage; do not convert it into an unexplained certainty badge.
- Keyboard, screen reader, focus, contrast and reduced-motion behavior are release requirements.
- SSE delivery is at least once; clients deduplicate by event ID and can recover with `Last-Event-ID`.
- Feedback is append-only and does not silently alter historical generated output.
- Logs, traces and metrics exclude source bytes, quotes, prompts, secrets and personally identifying content by default.
- Cross-tenant and public-share authorization tests are blocking.
- Scientific quality gates are blocking even when application tests and latency targets pass.
- A release with any fabricated quote or unauthorized source disclosure is rejected.

---

## File Structure

- `starter/services/api/src/citetrace_api/read_models/` — stable evidence and analysis projections.
- `starter/services/api/src/citetrace_api/streaming/` — durable SSE replay.
- `starter/services/api/src/citetrace_api/feedback/` — append-only feedback and adjudication queues.
- `starter/apps/web/src/features/reader/` — document, reference and evidence panes.
- `starter/apps/web/src/lib/api/` — generated contract client and SSE adapter.
- `starter/apps/web/tests/` — component, accessibility and browser tests.
- `starter/ops/` — deployment, dashboards, alerts, runbooks and load tests.
- `starter/e2e/` — user-journey fixtures and Playwright suites.

### Task 1: Evidence read models and contract-complete API

**Files:**
- Create: `starter/services/api/src/citetrace_api/read_models/__init__.py`
- Create: `starter/services/api/src/citetrace_api/read_models/evidence.py`
- Create: `starter/services/api/src/citetrace_api/read_models/references.py`
- Create: `starter/services/api/src/citetrace_api/db/repositories/read_models.py`
- Create: `starter/services/api/src/citetrace_api/routes/evidence.py`
- Create: `starter/services/api/tests/test_evidence_read_api.py`
- Create: `starter/services/api/tests/test_reference_map_api.py`
- Modify: `starter/services/api/src/citetrace_api/main.py`
- Modify: `contracts/openapi.yaml`

**Interfaces:**
- Consumes: audited evidence links, source spans, explanations, references and analysis records.
- Produces: list/detail evidence endpoints, citation/reference map, source-span locator and stable cursor pagination matching OpenAPI.

- [ ] **Step 1: Write failing evidence-list API tests**

```python
def test_list_returns_only_publishable_evidence_links(client: TestClient) -> None:
    response = client.get(
        f"/v1/analyses/{ANALYSIS_ID}/evidence-links?status=verified&limit=20",
        headers=auth_headers(WORKSPACE_ID),
    )
    assert response.status_code == 200
    body = response.json()
    assert all(item["status"] == "verified" for item in body["items"])
    assert all(item["audit_status"] in {"passed", "passed_with_warnings"} for item in body["items"])
    assert all("object_key" not in item for item in body["items"])
```

Add relation, reference, citation-anchor and reading-priority filters; cursor stability; blocked-link exclusion; and cross-workspace 404 behavior.

- [ ] **Step 2: Define read-model projections**

```python
@dataclass(frozen=True, slots=True)
class EvidenceCardView:
    id: UUID
    citation_anchor_id: UUID
    reference_entry_id: UUID
    status: EvidenceLinkStatus
    citation_intents: tuple[CitationIntent, ...]
    evidence_relation: EvidenceRelation
    headline: str
    citing_claim: ClaimView
    source_spans: tuple[SourceSpanView, ...]
    transformations: tuple[TransformationView, ...]
    confidence: ConfidenceVectorView
    limitations: tuple[LimitationView, ...]
    access_disclosure: AccessDisclosureView
```

Read models include only fields allowed for the actor and source display policy.

- [ ] **Step 3: Write failing reference-map tests**

Assert that `GET /v1/analyses/{id}/reference-map` returns:

- total and in-scope reference counts,
- role labels and reading priority,
- resolution/access/status summary,
- citation anchor IDs and counts,
- lineage edges only when independently verified,
- no inaccessible quote text.

- [ ] **Step 4: Implement cursor-based repository queries**

Use `(created_at, id)` or another immutable deterministic tuple. Encode cursor payload with a version and HMAC; reject malformed or filter-incompatible cursors with a stable 422 problem.

- [ ] **Step 5: Implement evidence detail and locator routes**

`GET /v1/evidence-links/{id}` returns the complete audited object. `GET /v1/source-spans/{id}/locator` returns only viewer-safe page, section, offsets and bounding boxes plus an asset-view token scoped to actor, asset and short expiry.

- [ ] **Step 6: Generate and validate OpenAPI client fixtures**

Export OpenAPI JSON and assert the evidence endpoints validate representative success, limited, review-required and inaccessible responses against the contract.

- [ ] **Step 7: Run API read-model tests**

Run:

```bash
python scripts/validate_package.py
cd starter/services/api
pytest tests/test_evidence_read_api.py tests/test_reference_map_api.py -v
pytest -q
```

Expected: filters, pagination, access disclosure and tenant isolation pass.

- [ ] **Step 8: Commit the read API**

```bash
git add contracts/openapi.yaml starter/services/api/src/citetrace_api/read_models \
  starter/services/api/src/citetrace_api/db/repositories/read_models.py \
  starter/services/api/src/citetrace_api/routes/evidence.py \
  starter/services/api/src/citetrace_api/main.py \
  starter/services/api/tests/test_evidence_read_api.py \
  starter/services/api/tests/test_reference_map_api.py
git commit -m "feat: expose audited evidence read models"
```

### Task 2: Durable SSE replay and analysis progress

**Files:**
- Create: `starter/services/api/src/citetrace_api/streaming/__init__.py`
- Create: `starter/services/api/src/citetrace_api/streaming/event_store.py`
- Create: `starter/services/api/src/citetrace_api/streaming/sse.py`
- Create: `starter/services/api/tests/test_sse_replay.py`
- Create: `starter/services/api/tests/test_progress_projection.py`
- Modify: `starter/services/api/src/citetrace_api/routes/analyses.py`
- Modify: `contracts/event_catalog.yaml`

**Interfaces:**
- Consumes: published outbox events and durable analysis state.
- Produces: ordered workspace-authorized SSE stream with replay, heartbeat and current-state recovery.

- [ ] **Step 1: Write failing replay tests**

```python
def test_stream_replays_after_last_event_id(client: TestClient) -> None:
    response = client.get(
        f"/v1/analyses/{ANALYSIS_ID}/stream",
        headers={**auth_headers(WORKSPACE_ID), "Last-Event-ID": SECOND_EVENT_ID},
    )
    events = parse_sse(response.text)
    assert [event.id for event in events] == [THIRD_EVENT_ID, FOURTH_EVENT_ID]
```

Add duplicate-delivery tolerance, unauthorized workspace, expired replay window, terminal state and reconnect tests.

- [ ] **Step 2: Define durable event ordering**

```python
@dataclass(frozen=True, slots=True)
class StreamEvent:
    id: UUID
    aggregate_id: UUID
    event_type: str
    schema_version: str
    sequence: int
    occurred_at: datetime
    payload: Mapping[str, object]
```

Allocate monotonically increasing sequence per analysis in the database transaction that publishes the event.

- [ ] **Step 3: Implement event replay repository**

```python
class EventStore:
    async def after(self, analysis_id: UUID, last_event_id: UUID | None, limit: int) -> list[StreamEvent]: ...
    async def wait_for_new(self, analysis_id: UUID, after_sequence: int, timeout_seconds: float) -> None: ...
```

Use PostgreSQL notification only as a wake-up hint; always read durable events after waking.

- [ ] **Step 4: Implement SSE serialization and heartbeat**

Emit `id`, `event`, `retry` and one JSON `data` line. Heartbeats are comment frames every 15 seconds. Set `Cache-Control: no-cache`, `X-Accel-Buffering: no` and disable compression for the stream path.

- [ ] **Step 5: Implement progress projection tests and logic**

Progress is derived from durable stage units. It never decreases within one pipeline version, and a terminal state reports 100%. A scope change creates a new analysis rather than resetting an existing progress stream.

- [ ] **Step 6: Run stream tests**

Run:

```bash
cd starter/services/api
pytest tests/test_sse_replay.py tests/test_progress_projection.py -v
pytest -q
```

Expected: replay, deduplication and monotonic progress pass.

- [ ] **Step 7: Commit durable streaming**

```bash
git add contracts/event_catalog.yaml starter/services/api/src/citetrace_api/streaming \
  starter/services/api/src/citetrace_api/routes/analyses.py \
  starter/services/api/tests/test_sse_replay.py starter/services/api/tests/test_progress_projection.py
git commit -m "feat: stream replayable analysis progress"
```

### Task 3: Typed web API client and reader state machine

**Files:**
- Create: `starter/apps/web/src/lib/api/types.ts`
- Create: `starter/apps/web/src/lib/api/client.ts`
- Create: `starter/apps/web/src/lib/api/sse.ts`
- Create: `starter/apps/web/src/features/reader/state.ts`
- Create: `starter/apps/web/src/features/reader/useAnalysis.ts`
- Create: `starter/apps/web/tests/api-client.test.ts`
- Create: `starter/apps/web/tests/reader-state.test.ts`
- Modify: `starter/apps/web/package.json`

**Interfaces:**
- Consumes: OpenAPI-compatible REST responses and event catalog SSE messages.
- Produces: typed query functions, reconnecting event stream and deterministic reader state.

- [ ] **Step 1: Add web test dependencies and scripts**

Add:

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "devDependencies": {
    "@testing-library/react": "^16.0.0",
    "jsdom": "^26.0.0",
    "vitest": "^3.0.0"
  }
}
```

Preserve existing build and typecheck scripts.

- [ ] **Step 2: Write failing API error tests**

```typescript
it("parses application/problem+json into a typed error", async () => {
  server.use(problemResponse(422, "reference_ambiguous"));
  await expect(api.getAnalysis(analysisId)).rejects.toMatchObject({
    status: 422,
    code: "reference_ambiguous",
  });
});
```

Also test aborted requests, invalid JSON, schema-version mismatch and 401/403 handling.

- [ ] **Step 3: Implement typed REST client**

```typescript
export class CiteTraceApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly instance?: string,
  ) {
    super(message);
  }
}

export async function getAnalysis(id: string, signal?: AbortSignal): Promise<Analysis>;
export async function listEvidenceLinks(id: string, query: EvidenceQuery, signal?: AbortSignal): Promise<EvidenceLinkPage>;
export async function getReferenceMap(id: string, signal?: AbortSignal): Promise<ReferenceMap>;
```

Validate required response fields at runtime and reject an unsupported schema version.

- [ ] **Step 4: Write failing SSE reconnection tests**

Test event-ID deduplication, exponential reconnect capped at 15 seconds, `Last-Event-ID` reuse, terminal-state closure and transition to REST refresh when replay expired.

- [ ] **Step 5: Implement the event-stream adapter**

Expose:

```typescript
export type AnalysisStream = {
  close(): void;
  subscribe(listener: (event: AnalysisEvent) => void): () => void;
};

export function openAnalysisStream(analysisId: string, options: StreamOptions): AnalysisStream;
```

Keep event parsing and reconnect logic separate from React.

- [ ] **Step 6: Write reader reducer tests**

States include `idle`, `loading`, `running`, `completed`, `completed_with_limits`, `failed`, `cancelled` and `reconnecting`. Duplicate/older event sequences are ignored. Evidence-link updates merge by ID without changing user selection.

- [ ] **Step 7: Implement reducer and hook**

The hook performs initial REST fetch, opens SSE while non-terminal, refreshes paginated evidence on relevant events and closes connections on unmount or terminal state.

- [ ] **Step 8: Run web unit and type tests**

Run:

```bash
corepack enable
pnpm --dir starter/apps/web install
pnpm --dir starter/apps/web test
pnpm --dir starter/apps/web typecheck
```

Expected: API, SSE and reducer tests pass.

- [ ] **Step 9: Commit typed reader state**

```bash
git add starter/apps/web/package.json starter/apps/web/src/lib/api \
  starter/apps/web/src/features/reader/state.ts starter/apps/web/src/features/reader/useAnalysis.ts \
  starter/apps/web/tests/api-client.test.ts starter/apps/web/tests/reader-state.test.ts
git commit -m "feat: add typed analysis client and stream state"
```

### Task 4: Production three-pane reader and exact source navigation

**Files:**
- Create: `starter/apps/web/src/features/reader/ReaderWorkspace.tsx`
- Create: `starter/apps/web/src/features/reader/ReferenceMapPane.tsx`
- Create: `starter/apps/web/src/features/reader/PaperPane.tsx`
- Create: `starter/apps/web/src/features/reader/EvidencePane.tsx`
- Create: `starter/apps/web/src/features/reader/EvidenceCard.tsx`
- Create: `starter/apps/web/src/features/reader/ConfidenceVector.tsx`
- Create: `starter/apps/web/src/features/reader/LimitationNotice.tsx`
- Create: `starter/apps/web/src/features/reader/pdf/DocumentViewer.tsx`
- Create: `starter/apps/web/src/features/reader/pdf/coordinateTransform.ts`
- Create: `starter/apps/web/tests/evidence-card.test.tsx`
- Create: `starter/apps/web/tests/coordinate-transform.test.ts`
- Modify: `starter/apps/web/src/app/page.tsx`
- Modify: `starter/apps/web/src/app/globals.css`
- Modify: `starter/apps/web/package.json`

**Interfaces:**
- Consumes: typed analysis, reference map, evidence cards and source-span locators.
- Produces: keyboard-accessible synchronized selection across reference list, citing PDF and source evidence detail.

- [ ] **Step 1: Add PDF.js dependency and worker configuration**

Add a pinned compatible `pdfjs-dist` dependency and configure the worker through a local bundled asset. Do not fetch the worker from a third-party CDN in production.

- [ ] **Step 2: Write failing evidence-card accessibility tests**

```typescript
it("exposes relation, access level, source location and confidence stages", () => {
  render(<EvidenceCard evidence={verifiedFixture} />);
  expect(screen.getByRole("heading", { name: verifiedFixture.headline })).toBeVisible();
  expect(screen.getByText("직접 지지")).toBeVisible();
  expect(screen.getByText("오픈 액세스 원문")).toBeVisible();
  expect(screen.getByText("관계 판정 88%")).toBeVisible();
  expect(screen.getByRole("button", { name: "원문 위치 열기" })).toBeEnabled();
});
```

Add limited, inaccessible, review-required, transformation and no-coordinate variants.

- [ ] **Step 3: Implement evidence-card information hierarchy**

Required order:

1. relation/status and access disclosure;
2. citation role;
3. exact citing claim;
4. exact source quote or explicit no-quote limitation;
5. relation explanation and scope differences;
6. transformations with paired spans;
7. stage confidence and reason codes;
8. reading priority and recommended sections;
9. source-navigation and feedback actions.

- [ ] **Step 4: Write failing coordinate-transform tests**

Test PDF points to CSS pixels across rotation 0/90/180/270, zoom changes, HiDPI scale and multiple bounding boxes. Assert boxes remain inside page bounds and retain reading order.

- [ ] **Step 5: Implement exact viewer navigation**

```typescript
export type SourceLocator = {
  page: number | null;
  boundingBoxes: BoundingBox[];
  startOffset: number;
  endOffset: number;
  sectionPath: string[];
};
```

When coordinates exist, navigate and highlight. When absent, navigate to page/section and show “exact PDF box unavailable” rather than fabricating a highlight.

- [ ] **Step 6: Implement reference map and synchronized selection**

Support filters for role, relation, status, access and priority. Selecting a citation anchor updates the evidence pane and scrolls the citing paper. Selecting a source span opens a source tab/viewer for the exact cited asset version.

- [ ] **Step 7: Implement responsive and reduced-motion layouts**

Desktop uses three panes. Medium screens use a docked evidence drawer. Mobile uses ordered tabs: Paper, References, Evidence. Preserve selected citation across layout changes and disable animated scrolling under `prefers-reduced-motion`.

- [ ] **Step 8: Run component, type and build checks**

Run:

```bash
pnpm --dir starter/apps/web test
pnpm --dir starter/apps/web typecheck
pnpm --dir starter/apps/web build
```

Expected: accessibility assertions, coordinate transforms and production build pass.

- [ ] **Step 9: Commit the production reader**

```bash
git add starter/apps/web/package.json starter/apps/web/src/features/reader \
  starter/apps/web/src/app/page.tsx starter/apps/web/src/app/globals.css \
  starter/apps/web/tests/evidence-card.test.tsx \
  starter/apps/web/tests/coordinate-transform.test.ts
git commit -m "feat: build inspectable three-pane evidence reader"
```

### Task 5: Append-only feedback and adjudication queue

**Files:**
- Create: `starter/services/api/src/citetrace_api/feedback/__init__.py`
- Create: `starter/services/api/src/citetrace_api/feedback/models.py`
- Create: `starter/services/api/src/citetrace_api/feedback/service.py`
- Create: `starter/services/api/src/citetrace_api/routes/feedback.py`
- Create: `starter/services/api/src/citetrace_api/db/repositories/feedback.py`
- Create: `starter/services/api/tests/test_feedback_api.py`
- Create: `starter/services/api/tests/test_adjudication_queue.py`
- Create: `starter/apps/web/src/features/feedback/EvidenceFeedbackDialog.tsx`
- Create: `starter/apps/web/tests/feedback-dialog.test.tsx`
- Modify: `contracts/openapi.yaml`

**Interfaces:**
- Consumes: actor, evidence link, feedback kind, optional proposed relation/span and comment.
- Produces: immutable feedback event, queue priority and user-visible receipt; generated evidence remains historically unchanged.

- [ ] **Step 1: Write failing feedback validation tests**

Test every feedback kind, comment length, proposed-relation taxonomy, source-span ownership, duplicate idempotency key, cross-workspace access and feedback on a deleted asset.

- [ ] **Step 2: Implement typed feedback command and repository**

```python
@dataclass(frozen=True, slots=True)
class SubmitFeedback:
    workspace_id: UUID
    actor_user_id: UUID
    evidence_link_id: UUID
    feedback_kind: FeedbackKind
    proposed_relation: EvidenceRelation | None
    proposed_source_span: ProposedSourceSpan | None
    comment: str | None
    idempotency_key: str


class FeedbackRepository:
    async def append(self, command: SubmitFeedback) -> FeedbackRecord: ...
```

Store feedback as a new event; never update relation/source span fields on the original evidence link.

- [ ] **Step 3: Write failing queue-priority tests**

Priority increases for fabricated-quote reports, wrong source, wrong resolution, contradiction/overgeneralization disputes, multiple independent reports and high-usage evidence links. “Unclear explanation” alone has lower scientific-risk priority.

- [ ] **Step 4: Implement adjudication projection**

```python
class AdjudicationQueueService:
    async def list(self, workspace_id: UUID, cursor: str | None, limit: int) -> AdjudicationPage: ...
    async def record_decision(self, command: AdjudicationDecisionCommand) -> UUID: ...
```

A decision creates a new adjudicated analysis/evidence version or marks feedback invalid; it does not erase the submitted event.

- [ ] **Step 5: Implement feedback dialog**

Use accessible radio groups, optional relation selector, exact source-span proposal and a plain-language privacy notice. After submission, show event ID and explain that review does not immediately rewrite the historical result.

- [ ] **Step 6: Validate contracts and run tests**

Run:

```bash
python scripts/validate_package.py
cd starter/services/api
pytest tests/test_feedback_api.py tests/test_adjudication_queue.py -v
cd ../../../starter/apps/web
pnpm test -- feedback-dialog.test.tsx
```

Expected: immutable feedback and prioritization tests pass.

- [ ] **Step 7: Commit feedback workflows**

```bash
git add contracts/openapi.yaml starter/services/api/src/citetrace_api/feedback \
  starter/services/api/src/citetrace_api/routes/feedback.py \
  starter/services/api/src/citetrace_api/db/repositories/feedback.py \
  starter/services/api/tests/test_feedback_api.py \
  starter/services/api/tests/test_adjudication_queue.py \
  starter/apps/web/src/features/feedback starter/apps/web/tests/feedback-dialog.test.tsx
git commit -m "feat: add append-only evidence feedback workflow"
```

### Task 6: Private notes, provenance-preserving export and revocable sharing

**Files:**
- Create: `starter/services/api/src/citetrace_api/collaboration/__init__.py`
- Create: `starter/services/api/src/citetrace_api/collaboration/models.py`
- Create: `starter/services/api/src/citetrace_api/collaboration/notes.py`
- Create: `starter/services/api/src/citetrace_api/exports/__init__.py`
- Create: `starter/services/api/src/citetrace_api/exports/models.py`
- Create: `starter/services/api/src/citetrace_api/exports/service.py`
- Create: `starter/services/api/src/citetrace_api/sharing/__init__.py`
- Create: `starter/services/api/src/citetrace_api/sharing/service.py`
- Create: `starter/services/api/src/citetrace_api/routes/collaboration.py`
- Create: `starter/services/api/src/citetrace_api/db/repositories/collaboration.py`
- Create: `starter/services/api/tests/test_private_notes.py`
- Create: `starter/services/api/tests/test_provenance_export.py`
- Create: `starter/services/api/tests/test_share_links.py`
- Create: `starter/apps/web/src/features/collaboration/NoteComposer.tsx`
- Create: `starter/apps/web/src/features/export/ExportDialog.tsx`
- Create: `starter/apps/web/tests/collaboration-policy.test.tsx`
- Modify: `contracts/openapi.yaml`
- Modify: `contracts/db/schema.sql`

**Interfaces:**
- Consumes: authenticated actor/workspace role, analysis/evidence/source access policies, provenance-bearing read models and export/share command.
- Produces: versioned private notes, policy-filtered JSON/Markdown exports, short-lived revocable share views and auditable receipts. It never republishes source text merely because an analysis can display it to its owner.

- [ ] **Step 1: Write failing private-note authorization and rendering tests**

Assert that a note can target an analysis, citation anchor, evidence link or source span; defaults to author-private visibility; workspace visibility requires an allowed role; cross-workspace targets return 404; deleted/revoked source assets prevent new source-bound notes; Markdown is sanitized with raw HTML, scripts, remote images and unsafe links disabled; edit creates a new version while preserving history.

- [ ] **Step 2: Implement versioned note contracts and repository**

```python
class NoteVisibility(StrEnum):
    PRIVATE = "private"
    WORKSPACE = "workspace"


@dataclass(frozen=True, slots=True)
class CreateNote:
    workspace_id: UUID
    actor_user_id: UUID
    target_type: Literal["analysis", "citation_anchor", "evidence_link", "source_span"]
    target_id: UUID
    visibility: NoteVisibility
    markdown: str
    idempotency_key: str


class CollaborationRepository:
    async def append_note(self, command: CreateNote) -> NoteVersion: ...
    async def list_notes(self, actor: Actor, target: NoteTarget) -> tuple[NoteView, ...]: ...
```

Persist immutable note versions and a current-version pointer. Store sanitized rendering separately from author input; never render untrusted HTML directly.

- [ ] **Step 3: Write failing export policy tests**

For JSON and Markdown exports, assert inclusion of claim, relation, transformation, confidence, limitation, source locator and provenance versions. Assert exclusion or truncation of private/source-restricted quotes, provider secrets, raw model output, object keys and user identity. A deleted asset produces a retained judgment with a revoked-source notice rather than stale redisplay. Repeated idempotency keys return the same export job.

- [ ] **Step 4: Implement asynchronous export service**

```python
class AnalysisExportService:
    async def request(self, command: RequestAnalysisExport) -> ExportJob: ...
    async def materialize(self, export_id: UUID) -> ExportArtifact: ...
```

Apply the strictest policy among workspace, source assets and requested destination. Write immutable export bytes to a tenant-scoped object key with checksum, expiration and audit record. Markdown uses plain text plus stable identifiers; JSON validates against a versioned export schema.

- [ ] **Step 5: Write failing share-link security tests**

Test cryptographically random token generation, hashed token storage, default expiry, explicit revocation, one-time policy re-evaluation on every access, rate limiting, no workspace enumeration, no indexing, no raw private file URL, and strict source quotation filtering. Verify a share created before a source revocation immediately stops displaying restricted evidence.

- [ ] **Step 6: Implement revocable policy-filtered sharing**

```python
class ShareService:
    async def create(self, command: CreateShare) -> CreatedShare: ...
    async def resolve(self, token: str, request_context: ShareRequestContext) -> SharedAnalysisView: ...
    async def revoke(self, share_id: UUID, actor: Actor) -> None: ...
```

Store only the token hash, policy snapshot, expiry and creator. Build the shared view at request time from authorized read models; never copy unrestricted private source content into a public table.

- [ ] **Step 7: Implement notes/export UI with explicit policy copy**

The note composer announces visibility, the export dialog lists included/excluded content before creation, and share creation requires explicit expiry and shows revocation controls. Do not use a generic “public” toggle. Add keyboard/focus/error tests and show export/share receipt IDs.

- [ ] **Step 8: Validate contracts and run collaboration tests**

Run:

```bash
python scripts/validate_package.py
cd starter/services/api
pytest tests/test_private_notes.py tests/test_provenance_export.py tests/test_share_links.py -v
cd ../../../starter/apps/web
pnpm test -- collaboration-policy.test.tsx
```

Expected: tenant/role, content-policy, provenance, revocation and UI disclosure tests pass.

- [ ] **Step 9: Commit safe collaboration surfaces**

```bash
git add contracts/openapi.yaml contracts/db/schema.sql \
  starter/services/api/src/citetrace_api/collaboration \
  starter/services/api/src/citetrace_api/exports \
  starter/services/api/src/citetrace_api/sharing \
  starter/services/api/src/citetrace_api/routes/collaboration.py \
  starter/services/api/src/citetrace_api/db/repositories/collaboration.py \
  starter/services/api/tests/test_private_notes.py \
  starter/services/api/tests/test_provenance_export.py \
  starter/services/api/tests/test_share_links.py \
  starter/apps/web/src/features/collaboration \
  starter/apps/web/src/features/export \
  starter/apps/web/tests/collaboration-policy.test.tsx
git commit -m "feat: add policy-safe notes exports and sharing"
```

### Task 7: Browser accessibility and end-to-end trust journeys

**Files:**
- Create: `starter/e2e/playwright.config.ts`
- Create: `starter/e2e/package.json`
- Create: `starter/e2e/tests/analyze-paper.spec.ts`
- Create: `starter/e2e/tests/limited-source.spec.ts`
- Create: `starter/e2e/tests/keyboard-reader.spec.ts`
- Create: `starter/e2e/tests/tenant-isolation.spec.ts`
- Create: `starter/e2e/fixtures/seed.ts`
- Create: `starter/e2e/fixtures/verified-analysis.json`
- Create: `starter/e2e/fixtures/limited-analysis.json`

**Interfaces:**
- Consumes: running API/web and deterministic seeded analyses.
- Produces: browser-level proof of critical user and security journeys.

- [ ] **Step 1: Add the Playwright test project**

Pin Playwright, provide web/API base URLs and start commands. Capture trace and screenshot only on failure, with fixtures containing synthetic text rather than private papers.

- [ ] **Step 2: Write the core analysis journey**

The test uploads a synthetic born-digital PDF, starts Understand mode, observes progress, selects reference `[12]`, verifies the citing claim/source quote/relation/access/confidence and opens the exact source location.

- [ ] **Step 3: Write the limited-source journey**

Seed an inaccessible source and assert:

- no quote is displayed,
- relation reads “원문 접근 불가,”
- limitation and recovery action are visible,
- the UI does not imply the claim was supported or contradicted.

- [ ] **Step 4: Write keyboard and screen-reader semantics tests**

Navigate top bar, reference list, citing marker, evidence card, confidence details and feedback dialog using only keyboard. Assert focus is visible, selected state is announced, headings are hierarchical and relation/status are not conveyed by color alone.

- [ ] **Step 5: Write browser tenant-isolation test**

Authenticate as workspace B, request a known workspace A analysis/evidence/source locator and assert 404 with no title, quote, identifier or timing-dependent distinction.

- [ ] **Step 6: Run browser tests**

Run:

```bash
pnpm --dir starter/e2e install
pnpm --dir starter/e2e exec playwright install --with-deps chromium
pnpm --dir starter/e2e test
```

Expected: all core, limited, accessibility and tenant tests pass.

- [ ] **Step 7: Commit trust journeys**

```bash
git add starter/e2e
git commit -m "test: cover reader trust journeys end to end"
```

### Task 8: OpenTelemetry, safe metrics, alerts and cost ledger

**Files:**
- Create: `starter/services/api/src/citetrace_api/observability/__init__.py`
- Create: `starter/services/api/src/citetrace_api/observability/logging.py`
- Create: `starter/services/api/src/citetrace_api/observability/tracing.py`
- Create: `starter/services/api/src/citetrace_api/observability/metrics.py`
- Create: `starter/services/api/tests/test_log_redaction.py`
- Create: `starter/services/api/tests/test_metric_labels.py`
- Create: `starter/ops/dashboards/analysis-overview.json`
- Create: `starter/ops/alerts/citetrace.rules.yaml`
- Create: `starter/ops/runbooks/analysis-stalled.md`
- Create: `starter/ops/runbooks/provider-degraded.md`
- Create: `starter/ops/runbooks/quality-gate-regression.md`
- Modify: `starter/services/api/pyproject.toml`

**Interfaces:**
- Consumes: request/stage/model/provider/source events.
- Produces: safe structured logs, distributed traces, bounded-cardinality metrics, alerts and cost records.

- [ ] **Step 1: Write failing redaction tests**

Assert that logs redact:

- Authorization and API-key headers,
- signed URL query parameters,
- object-store credentials,
- source quotes and normalized paper text,
- raw model prompts/outputs,
- user email and display name.

Allow trace ID, workspace pseudonym, artifact UUID, stage, status, provider, model ID, token counts, latency, cost and stable reason codes.

- [ ] **Step 2: Implement structured logging filter**

```python
class SafeLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.msg)
        record.args = redact(record.args)
        return True
```

Prefer explicit structured event builders over generic object serialization.

- [ ] **Step 3: Write failing metric-cardinality tests**

Reject labels containing analysis IDs, document IDs, URLs, titles, DOIs, user IDs or arbitrary error messages. Approved labels include environment, stage, status, provider, access level, relation and stable reason code.

- [ ] **Step 4: Instrument traces and metrics**

Create spans for API request, stage attempt, provider request, object operation, parser request, model execution and audit. Propagate W3C trace context through outbox payload metadata without exposing private content.

Required metrics:

- analysis created/completed/failed/limited counts,
- stage duration and queue delay,
- provider latency/error/quota outcomes,
- GROBID latency/503 rate,
- model tokens/cost/schema failures,
- evidence verified/limited/review/blocked counts,
- quote validation failures,
- unsupported-statement audit blocks,
- SSE active connections/reconnects,
- source bytes and retention-deletion backlog.

- [ ] **Step 5: Implement per-analysis cost ledger**

Aggregate parser, provider, embedding, model, storage and egress cost from immutable execution records. Display operator cost, not model-estimated values, and preserve currency/source timestamp.

- [ ] **Step 6: Add alert rules and runbooks**

Alert on stalled analyses, queue age, provider error spike, quote validation failure, audit-block spike, cross-tenant test failure, storage deletion backlog, model schema failure and daily cost anomaly. Each alert links one specific runbook with triage, mitigation, verification and rollback steps.

- [ ] **Step 7: Run observability tests**

Run:

```bash
cd starter/services/api
pytest tests/test_log_redaction.py tests/test_metric_labels.py -v
pytest -q
```

Expected: private content never appears and metric labels remain bounded.

- [ ] **Step 8: Commit production telemetry**

```bash
git add starter/services/api/pyproject.toml \
  starter/services/api/src/citetrace_api/observability \
  starter/services/api/tests/test_log_redaction.py \
  starter/services/api/tests/test_metric_labels.py starter/ops
git commit -m "feat: add safe observability and cost controls"
```

### Task 9: Security, retention and deletion enforcement

**Files:**
- Create: `starter/services/api/src/citetrace_api/security/headers.py`
- Create: `starter/services/api/src/citetrace_api/security/upload_tokens.py`
- Create: `starter/services/api/src/citetrace_api/retention/service.py`
- Create: `starter/services/api/src/citetrace_api/retention/worker.py`
- Create: `starter/services/api/tests/test_security_headers.py`
- Create: `starter/services/api/tests/test_asset_view_tokens.py`
- Create: `starter/services/api/tests/test_retention_deletion.py`
- Create: `starter/ops/runbooks/source-takedown.md`
- Create: `starter/ops/runbooks/privacy-delete-request.md`
- Modify: `starter/apps/web/next.config.ts`
- Modify: `starter/compose.yaml`

**Interfaces:**
- Consumes: workspace retention profile, deletion/takedown request and short-lived source-view authorization.
- Produces: CSP/security headers, scoped asset tokens, tombstones, byte deletion and audited deletion completion.

- [ ] **Step 1: Write failing security-header tests**

Require CSP with no unsafe script execution, frame-ancestors denial, strict transport security in production, no-sniff, referrer policy, permissions policy and private cache controls for document/evidence pages.

- [ ] **Step 2: Implement API/web header policies**

Next.js and FastAPI use environment-aware header builders from one documented policy. Permit PDF.js workers and local assets explicitly; do not loosen CSP globally for one component.

- [ ] **Step 3: Write failing asset-view token tests**

Token claims include actor, workspace, asset, action, expiry and nonce. Reject wrong actor/workspace/asset, replay after single-use when configured, expired token and deleted asset. Do not put source URLs or object keys in the token.

- [ ] **Step 4: Implement scoped source-view authorization**

Use signed short-lived tokens only after normal authorization. The object proxy rechecks asset status and source display policy before streaming, supports byte ranges for PDF.js and returns private cache headers.

- [ ] **Step 5: Write failing retention/deletion tests**

Test:

- expired upload bytes are tombstoned before deletion,
- active legal hold prevents deletion,
- derived parsed/chunk/span artifacts become unavailable when their asset is deleted,
- feedback/audit records retain non-content identifiers as policy allows,
- backup expiry is documented and bounded,
- repeated deletion jobs are idempotent.

- [ ] **Step 6: Implement retention worker**

```python
class RetentionService:
    async def plan_batch(self, now: datetime, limit: int) -> list[DeletionPlan]: ...
    async def execute(self, plan: DeletionPlan) -> DeletionOutcome: ...
```

Set `deleted_at` and block new reads before object deletion. After confirmed object deletion, remove or cryptographically erase content-bearing normalized artifacts while preserving an audit event with hashes and policy version.

- [ ] **Step 7: Run security/deletion tests**

Run:

```bash
cd starter/services/api
pytest tests/test_security_headers.py tests/test_asset_view_tokens.py \
  tests/test_retention_deletion.py -v
pytest -q
```

Expected: scoped access, tombstone-first deletion and idempotency pass.

- [ ] **Step 8: Commit security and lifecycle enforcement**

```bash
git add starter/services/api/src/citetrace_api/security \
  starter/services/api/src/citetrace_api/retention \
  starter/services/api/tests/test_security_headers.py \
  starter/services/api/tests/test_asset_view_tokens.py \
  starter/services/api/tests/test_retention_deletion.py \
  starter/apps/web/next.config.ts starter/compose.yaml starter/ops/runbooks
git commit -m "feat: enforce source access and retention lifecycle"
```

### Task 10: Gold-set evaluator and blocking release gate

**Files:**
- Create: `starter/services/api/src/citetrace_api/evaluation/metrics.py`
- Create: `starter/services/api/src/citetrace_api/evaluation/release_gate.py`
- Create: `starter/services/api/tests/test_evaluation_metrics.py`
- Create: `starter/services/api/tests/test_release_gate.py`
- Create: `scripts/run_release_evaluation.py`
- Create: `starter/ops/release/release-checklist.md`
- Modify: `starter/.github/workflows/ci.yml`

**Interfaces:**
- Consumes: hidden test predictions, adjudicated gold records and `eval/rubric.yaml`.
- Produces: versioned metrics report, per-slice failures and pass/fail release decision.

- [ ] **Step 1: Write failing metric tests**

Cover citation-anchor precision/recall, resolution top-1 accuracy, evidence Recall@5, relation macro-F1, inaccessible abstention accuracy, unsupported statement rate, fabricated quote count, calibration error and selective accuracy/coverage.

- [ ] **Step 2: Implement deterministic metrics**

```python
@dataclass(frozen=True, slots=True)
class EvaluationReport:
    dataset_version: str
    pipeline_version: str
    metrics: Mapping[str, float]
    slices: Mapping[str, Mapping[str, float]]
    blocking_failures: tuple[str, ...]
    quality_target_failures: tuple[str, ...]
```

Compute domain, access-level, multi-reference, relation, evidence-type, parse-grade and source-version slices.

- [ ] **Step 3: Write failing release-gate tests**

Assert immediate failure for one fabricated quote, one cross-tenant access failure, schema-valid rate below 1.0, unsupported statement rate above 0.02 and inaccessible false-full-text claims above zero. Quality target failures require an explicit signed waiver that cannot override blocking metrics.

- [ ] **Step 4: Implement release decision**

Load thresholds only from `eval/rubric.yaml`, include its SHA-256 in the report and produce machine-readable JSON plus a concise Markdown summary. Fail closed when a required metric is missing.

- [ ] **Step 5: Add CI evaluation jobs**

Pull the encrypted/controlled test-set artifact, run the frozen pipeline configuration, compute metrics, upload the report and block promotion. Development pull requests run a smaller public/synthetic regression set; release candidates run the full hidden test set.

- [ ] **Step 6: Add the release checklist**

Require:

- contract, unit, integration, browser and load tests;
- dependency/security scans;
- migration/RLS verification;
- gold-set release gate;
- provider/license/source-policy review;
- rollback artifact and database compatibility;
- dashboards/alerts/runbooks verified;
- exact versions and checksums recorded.

- [ ] **Step 7: Run evaluator tests**

Run:

```bash
cd starter/services/api
pytest tests/test_evaluation_metrics.py tests/test_release_gate.py -v
cd ../../..
python scripts/run_release_evaluation.py \
  --gold eval/sample_cases.jsonl \
  --predictions eval/sample_predictions.jsonl \
  --rubric eval/rubric.yaml \
  --output /tmp/citetrace-evaluation.json
```

Expected: synthetic sample passes its applicable contract checks and the report explicitly states that it is not a scientific performance result.

- [ ] **Step 8: Commit the quality release gate**

```bash
git add starter/services/api/src/citetrace_api/evaluation \
  starter/services/api/tests/test_evaluation_metrics.py \
  starter/services/api/tests/test_release_gate.py scripts/run_release_evaluation.py \
  starter/ops/release/release-checklist.md starter/.github/workflows/ci.yml
git commit -m "feat: block releases on scientific quality gates"
```

### Task 11: Capacity, resilience and production deployment proof

**Files:**
- Create: `starter/ops/load/analysis_load.py`
- Create: `starter/ops/load/sse_load.js`
- Create: `starter/ops/deploy/base/api.yaml`
- Create: `starter/ops/deploy/base/worker.yaml`
- Create: `starter/ops/deploy/base/web.yaml`
- Create: `starter/ops/deploy/base/network-policy.yaml`
- Create: `starter/ops/deploy/base/pod-disruption-budget.yaml`
- Create: `starter/ops/runbooks/rollback.md`
- Create: `starter/ops/runbooks/database-restore.md`
- Create: `starter/ops/runbooks/grobid-capacity.md`
- Create: `starter/ops/resilience/game-day.md`

**Interfaces:**
- Consumes: release image digests, production-like infrastructure and synthetic paper workloads.
- Produces: measured capacity envelope, resilience evidence and reproducible deployment manifests.

- [ ] **Step 1: Define workload profiles**

Profiles:

- small: 8 pages, 25 references, 5 in-scope citations;
- medium: 20 pages, 60 references, 15 in-scope citations;
- boundary: 60 pages, 150 references, 40 in-scope citations;
- mixed-access: full text, abstract-only and inaccessible references;
- burst: 20 concurrent uploads followed by 200 SSE clients.

Use synthetic or redistribution-approved fixtures only.

- [ ] **Step 2: Implement API/worker load test**

Measure upload latency, queue delay, stage durations, completion latency, provider/model concurrency, database connections, GROBID 503 behavior, memory and cost per analysis. Fail the test on data corruption, duplicate evidence links or unbounded queue growth.

- [ ] **Step 3: Implement SSE load test**

Open 200 connections, force reconnects, verify event ordering/deduplication and measure connection memory, heartbeat delivery and replay latency.

- [ ] **Step 4: Create least-privilege deployment manifests**

Separate web, API and worker service accounts; read-only root filesystems; non-root users; resource requests/limits; network policy; secret references; health/readiness probes; disruption budgets; autoscaling on queue age and CPU; no public ingress to PostgreSQL, Redis, object storage or GROBID.

- [ ] **Step 5: Run resilience scenarios**

Execute and document:

- GROBID 503 and restart,
- one metadata provider unavailable,
- model provider timeout,
- Redis restart,
- worker crash after commit,
- PostgreSQL failover,
- object-store transient failure,
- deployment rollback,
- expired credential rotation.

Verify idempotent recovery and accurate user-visible limitations.

- [ ] **Step 6: Test backup and restore**

Restore PostgreSQL and object-store backups into an isolated environment, verify checksum-linked assets and evidence spans, run RLS tests and record recovery point/time. Private deleted content must not reappear beyond documented backup retention.

- [ ] **Step 7: Record capacity envelope**

Write measured values for supported concurrent analyses, pages/hour, references/hour, SSE clients, p95 stage latency and cost bands. Do not convert estimates into contractual claims without production measurements.

- [ ] **Step 8: Commit deployment and resilience proof**

```bash
git add starter/ops/load starter/ops/deploy starter/ops/runbooks starter/ops/resilience
git commit -m "ops: add capacity and resilience production proof"
```

## Plan Acceptance Gate

Run:

```bash
python scripts/validate_package.py
cd starter/services/api
pytest -q
ruff check src tests
mypy src
cd ../../../starter/apps/web
pnpm test
pnpm typecheck
pnpm build
cd ../../e2e
pnpm test
```

Accept the plan only when:

- users can move from a citing marker to the exact cited-source location and inspect access/version/provenance;
- limited or inaccessible sources never display invented evidence or certainty;
- SSE replay and duplicate handling work after reconnect;
- all reader functions work by keyboard and expose semantic status independent of color;
- feedback is immutable and adjudication produces new versioned decisions;
- logs/traces/metrics contain no private paper text or secrets;
- retention, deletion and takedown workflows are tested and auditable;
- blocking scientific, security and tenant-isolation release gates pass;
- production deployment, load, rollback and restore evidence is recorded.
