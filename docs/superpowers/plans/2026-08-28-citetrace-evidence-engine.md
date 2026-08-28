# CiteTrace Evidence Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the evidence-first analysis engine that extracts atomic citing claims, retrieves exact passages from the resolved source version, judges scope-aware relations, explains adoption or change, calibrates uncertainty and blocks unsupported prose.

**Architecture:** Deterministic document artifacts and retrieval precede all scholarly judgments. Model tasks run through a versioned gateway with strict JSON Schema validation, privacy policy and audit records. Accepted evidence is represented as immutable source spans; relation, transformation and explanation records reference those spans instead of embedding unverifiable prose.

**Tech Stack:** Python 3.13, PostgreSQL 18 + pgvector, PostgreSQL full-text search, Pydantic, model-provider abstraction, JSON Schema, NumPy/scikit-learn for calibration, pytest.

**Spec:** `docs/superpowers/specs/2026-08-28-citetrace-product-system-design.md`, `docs/03_DOMAIN_TAXONOMY.md`, `docs/05_AGENT_AI_PIPELINE.md`, `docs/06_DATA_MODEL_PROVENANCE.md`, `docs/09_EVALUATION_GOLDSET_QA.md`, `docs/15_PROMPT_PACK_GUIDE.md`, `contracts/schemas/evidence-link.v1.schema.json`, `prompts/`

## Global Constraints

- Every user-visible material statement must reference validated source or citing spans, or be explicitly marked as inference or limitation.
- Exact quotes are copied only from immutable assets and validated against exact offsets before persistence and display.
- No relation label may be inferred from title, abstract topic similarity or citation intent alone.
- The model cannot introduce artifact IDs, labels, candidates or quotes absent from its input.
- Multi-reference citation clusters are decomposed and judged target by target.
- Claim qualifiers, negation, quantities, datasets, metrics, populations, time and modality are preserved.
- Abstract-only sources may support only propositions actually present in the abstract.
- A confidence vector exposes stage scores; the weakest stage can cap the publication status.
- `inaccessible_source`, `insufficient_evidence` and `review_required` are first-class outcomes, not failures to hide.
- Generator and final auditor model executions must be independent under the configured routing policy.

---

## File Structure

- `starter/services/api/src/citetrace_api/models/` — model gateway, schemas, privacy and execution records.
- `starter/services/api/src/citetrace_api/claims/` — context windows and atomic claim extraction.
- `starter/services/api/src/citetrace_api/retrieval/` — chunks, lexical/vector search, query plans and reranking.
- `starter/services/api/src/citetrace_api/verification/` — relation, scope and transformation decisions.
- `starter/services/api/src/citetrace_api/explanations/` — statement-level grounded output.
- `starter/services/api/src/citetrace_api/audit/` — blocking publication checks.
- `starter/services/api/src/citetrace_api/calibration/` — stage confidence and thresholds.
- `starter/services/api/tests/fixtures/evidence/` — synthetic and licensed test artifacts.

### Task 1: Versioned model gateway and structured-output enforcement

**Files:**
- Create: `starter/services/api/src/citetrace_api/models/__init__.py`
- Create: `starter/services/api/src/citetrace_api/models/contracts.py`
- Create: `starter/services/api/src/citetrace_api/models/gateway.py`
- Create: `starter/services/api/src/citetrace_api/models/privacy.py`
- Create: `starter/services/api/src/citetrace_api/models/execution_repository.py`
- Create: `starter/services/api/tests/test_model_gateway.py`
- Create: `starter/services/api/tests/test_model_privacy.py`
- Modify: `starter/services/api/src/citetrace_api/config.py`

**Interfaces:**
- Consumes: prompt template ID/version, validated input object, output schema, workspace policy and route profile.
- Produces: typed structured output and immutable `ModelExecutionRecord`; no model-specific type leaks into domain modules.

- [ ] **Step 1: Write failing schema and ID-containment tests**

```python
@pytest.mark.anyio
async def test_gateway_rejects_artifact_id_not_present_in_input(gateway: ModelGateway) -> None:
    with pytest.raises(ModelOutputViolation, match="unknown_artifact_id"):
        await gateway.execute(
            ModelTask(
                task_name="relation_verification",
                prompt_id="relation_verifier",
                prompt_version="1.0.0",
                input_payload={"source_spans": [{"id": str(ALLOWED_SPAN), "quote": "exact"}]},
                output_schema=RELATION_SCHEMA,
                allowed_artifact_ids=frozenset({ALLOWED_SPAN}),
            )
        )
```

Add tests for invalid JSON, unknown enum value, extra property, quote modification, one bounded repair attempt, generator/auditor route separation and redacted logs.

- [ ] **Step 2: Define provider-neutral contracts**

```python
@dataclass(frozen=True, slots=True)
class ModelTask:
    task_name: str
    prompt_id: str
    prompt_version: str
    input_payload: Mapping[str, object]
    output_schema: Mapping[str, object]
    allowed_artifact_ids: frozenset[UUID]
    privacy_classification: str = "private_document_text"


class ModelProvider(Protocol):
    name: str
    async def generate_json(self, request: ProviderModelRequest) -> ProviderModelResponse: ...


class ModelGateway:
    async def execute[T: BaseModel](self, task: ModelTask, output_type: type[T]) -> T: ...
```

- [ ] **Step 3: Implement prompt loading and hash validation**

Load only prompt files registered at process start. Compute SHA-256 for the template and store template ID, semantic version and hash in each execution record. Refuse duplicate IDs with different contents for the same version.

- [ ] **Step 4: Implement privacy routing**

```python
class PrivacyPolicy:
    def authorize(
        self,
        workspace_profile: str,
        provider: str,
        task_name: str,
        contains_private_text: bool,
    ) -> PrivacyDecision: ...
```

Deny document text transmission to providers not approved by `config/model-routing.example.yaml`. Store safe input artifact hashes by default; raw prompts and raw outputs remain absent unless an explicitly authorized secure-debug profile is active.

- [ ] **Step 5: Implement strict output validation**

Sequence:

1. parse exactly one JSON value;
2. validate Draft 2020-12 JSON Schema;
3. validate Pydantic domain model;
4. check all artifact IDs against the allowlist;
5. check quote fields are exact supplied strings;
6. permit one schema-repair request containing validation errors and the original output hash;
7. classify a second failure as `model_output_invalid`.

- [ ] **Step 6: Persist model execution provenance**

Record purpose, provider, model ID/version, route, prompt version/hash, input hashes, output schema version, token usage, latency, cost, validation status, retry count and privacy policy. Do not store secrets or paper text in standard logs.

- [ ] **Step 7: Run gateway tests**

Run:

```bash
cd starter/services/api
pytest tests/test_model_gateway.py tests/test_model_privacy.py -v
pytest -q
```

Expected: all schema, artifact, privacy and audit-record tests pass.

- [ ] **Step 8: Commit the model boundary**

```bash
git add starter/services/api/src/citetrace_api/models \
  starter/services/api/src/citetrace_api/config.py \
  starter/services/api/tests/test_model_gateway.py starter/services/api/tests/test_model_privacy.py
git commit -m "feat: enforce versioned structured model execution"
```

### Task 2: Citation context and atomic claim extraction

**Files:**
- Create: `starter/services/api/src/citetrace_api/claims/__init__.py`
- Create: `starter/services/api/src/citetrace_api/claims/context.py`
- Create: `starter/services/api/src/citetrace_api/claims/models.py`
- Create: `starter/services/api/src/citetrace_api/claims/extractor.py`
- Create: `starter/services/api/src/citetrace_api/db/repositories/claims.py`
- Create: `starter/services/api/tests/test_claim_context.py`
- Create: `starter/services/api/tests/test_claim_extractor.py`
- Create: `starter/services/api/tests/fixtures/evidence/citing-contexts.jsonl`

**Interfaces:**
- Consumes: normalized parsed document, citation cluster/anchor and target reference entry.
- Produces: exact `CitingClaim` records with qualifiers, target association, boundary confidence and extractor provenance.

- [ ] **Step 1: Write failing context-window tests**

```python
def test_context_preserves_absolute_offsets_and_anchor() -> None:
    window = build_context_window(
        normalized_text=DOCUMENT_TEXT,
        sentence_spans=SENTENCE_SPANS,
        cluster_start=120,
        cluster_end=124,
        previous_sentences=1,
        next_sentences=1,
    )
    assert window.text[window.anchor_start_local:window.anchor_end_local] == "[12]"
    assert window.absolute_start + window.anchor_start_local == 120
```

Add tests for section boundaries, footnotes, paragraph-first citations, author-year markers and a cluster inside a table caption.

- [ ] **Step 2: Define claim and qualifier models**

```python
class QualifierKind(StrEnum):
    POPULATION = "population"
    DATASET = "dataset"
    TASK = "task"
    METRIC = "metric"
    TIME = "time"
    MODALITY = "modality"
    CONDITION = "condition"
    HEDGE = "hedge"
    NEGATION = "negation"
    QUANTITY = "quantity"


@dataclass(frozen=True, slots=True)
class ExtractedClaim:
    text: str
    start_offset: int
    end_offset: int
    page: int | None
    qualifiers: tuple[ClaimQualifier, ...]
    target_associations: tuple[TargetAssociation, ...]
    boundary_confidence: float
```

- [ ] **Step 3: Write failing extraction validation tests**

Assert that the extractor rejects output when:

- claim text is not the exact citing-document substring,
- offsets cross the context window,
- a target reference ID is absent from the cluster,
- a model removes “may,” “not,” a dataset or numerical bound,
- two coordinated claims are returned as one when independently verifiable,
- an empty result lacks a limitation code.

- [ ] **Step 4: Implement `ClaimExtractor` through the model gateway**

```python
class ClaimExtractor:
    async def extract(
        self,
        parsed_document_id: UUID,
        citation_cluster_id: UUID,
        trace_id: str,
    ) -> ClaimExtractionOutcome: ...
```

Use `prompts/01_claim_extractor.md`. Validate exact substrings against the normalized document and calculate a deterministic qualifier-preservation score from matched surface spans.

- [ ] **Step 5: Implement multi-reference target association**

Create one claim-target record per defensible association. `shared_cluster` remains reviewable; `uncertain` does not proceed to automatic direct-support publication unless the user confirms the association or later syntax rules disambiguate it.

- [ ] **Step 6: Persist claims idempotently**

Use input fingerprint: parsed-document SHA, cluster ID, target reference IDs, extractor name/version and prompt version. Preserve earlier claim versions when the extractor changes.

- [ ] **Step 7: Run context and extraction tests**

Run:

```bash
cd starter/services/api
pytest tests/test_claim_context.py tests/test_claim_extractor.py -v
pytest -q
```

Expected: exact offsets, qualifiers and target associations pass.

- [ ] **Step 8: Commit claim extraction**

```bash
git add starter/services/api/src/citetrace_api/claims \
  starter/services/api/src/citetrace_api/db/repositories/claims.py \
  starter/services/api/tests/test_claim_context.py starter/services/api/tests/test_claim_extractor.py \
  starter/services/api/tests/fixtures/evidence/citing-contexts.jsonl
git commit -m "feat: extract qualifier-preserving citing claims"
```

### Task 3: Source chunking and hybrid lexical/vector index

**Files:**
- Create: `starter/services/api/src/citetrace_api/retrieval/__init__.py`
- Create: `starter/services/api/src/citetrace_api/retrieval/chunking.py`
- Create: `starter/services/api/src/citetrace_api/retrieval/embeddings.py`
- Create: `starter/services/api/src/citetrace_api/retrieval/index.py`
- Create: `starter/services/api/src/citetrace_api/db/repositories/chunks.py`
- Create: `starter/services/api/tests/test_evidence_chunking.py`
- Create: `starter/services/api/tests/test_hybrid_index.py`
- Modify: `starter/services/api/src/citetrace_api/config.py`

**Interfaces:**
- Consumes: exact parsed source version and structure nodes.
- Produces: source chunks with offsets, evidence type, section path, lexical index and versioned embedding.

- [ ] **Step 1: Write failing structure-aware chunk tests**

Test that:

- paragraphs are split only when token limits require it;
- section headings remain in chunk metadata, not duplicated into quotes;
- equations, algorithms, captions and table regions receive distinct evidence types;
- chunks overlap only within a structural node;
- every chunk text equals the exact parsed-document substring at offsets;
- abstract-only sources create only `abstract_span` chunks.

- [ ] **Step 2: Define chunker settings and output**

```python
@dataclass(frozen=True, slots=True)
class ChunkingProfile:
    maximum_tokens: int = 420
    overlap_tokens: int = 64
    minimum_tokens: int = 24
    preserve_sentence_boundaries: bool = True


class SourceChunker:
    def chunk(self, document: ParsedDocumentView, profile: ChunkingProfile) -> list[SourceChunkDraft]: ...
```

- [ ] **Step 3: Implement exact structural chunking**

Use the configured tokenizer only for boundary selection. Persist normalized offsets and text SHA; never reconstruct source text from model-generated summaries.

- [ ] **Step 4: Write failing embedding policy tests**

Assert that embedding requests:

- are denied when the workspace/provider policy forbids private text,
- include embedding model/profile version,
- batch within configured token and item limits,
- retry transient failures without duplicating rows,
- leave `embedding=NULL` while retaining lexical search when embedding fails.

- [ ] **Step 5: Implement embedding provider protocol**

```python
class EmbeddingProvider(Protocol):
    async def embed(self, texts: Sequence[str], profile: str, trace_id: str) -> list[list[float]]: ...
```

Validate vector dimension before persistence. The initial database contract uses 1536 dimensions; changing dimensions requires a new column/profile migration rather than mixed vectors in one index.

- [ ] **Step 6: Write failing hybrid search tests**

Create a fixture where lexical search catches an exact dataset/metric phrase and vector search catches a paraphrase. Assert reciprocal-rank fusion returns both, preserves source access and excludes chunks from a different work version or tenant.

- [ ] **Step 7: Implement repository hybrid search**

```python
class HybridEvidenceIndex:
    async def search(
        self,
        work_version_id: UUID,
        lexical_queries: Sequence[str],
        query_embeddings: Sequence[Sequence[float]],
        evidence_types: frozenset[EvidenceType],
        limit_per_channel: int = 30,
    ) -> list[RetrievedChunk]: ...
```

Use PostgreSQL `websearch_to_tsquery`, cosine distance and reciprocal-rank fusion. Apply work-version and access-level filters in SQL before ranking.

- [ ] **Step 8: Run chunk/index tests**

Run:

```bash
cd starter/services/api
pytest tests/test_evidence_chunking.py tests/test_hybrid_index.py -v
pytest -q
```

Expected: exact offsets, access isolation and hybrid retrieval tests pass.

- [ ] **Step 9: Commit the retrieval index**

```bash
git add starter/services/api/src/citetrace_api/retrieval \
  starter/services/api/src/citetrace_api/db/repositories/chunks.py \
  starter/services/api/src/citetrace_api/config.py \
  starter/services/api/tests/test_evidence_chunking.py starter/services/api/tests/test_hybrid_index.py
git commit -m "feat: index exact source chunks for hybrid retrieval"
```

### Task 4: Query planning, reranking and exact source-span selection

**Files:**
- Create: `starter/services/api/src/citetrace_api/retrieval/query_planner.py`
- Create: `starter/services/api/src/citetrace_api/retrieval/reranker.py`
- Create: `starter/services/api/src/citetrace_api/retrieval/span_selector.py`
- Create: `starter/services/api/src/citetrace_api/db/repositories/evidence_candidates.py`
- Create: `starter/services/api/tests/test_query_planner.py`
- Create: `starter/services/api/tests/test_evidence_reranker.py`
- Create: `starter/services/api/tests/test_source_span_selector.py`

**Interfaces:**
- Consumes: `CitingClaim`, citation intents, resolved work version and indexed chunks.
- Produces: persisted query plan, retained ranked candidates and one or more validated exact `SourceSpan` records.

- [ ] **Step 1: Write failing query-plan preservation tests**

Given “Method A did not improve F1 on Dataset Q after 2022,” assert that the plan retains `Method A`, `did not improve`, `F1`, `Dataset Q`, `after 2022`, includes Results/table hints and creates a contrast query. Reject plans that broaden the claim to generic performance.

- [ ] **Step 2: Implement query planner through the gateway**

Use `prompts/04_evidence_query_planner.md`, validate closed evidence types and cap to 5 lexical, 3 semantic and 3 contrast queries. Persist the exact plan and model execution ID.

- [ ] **Step 3: Write failing reranker tests**

Create candidates where:

- a topically similar paragraph lacks the named dataset;
- a table row contains the exact metric and values;
- a paragraph contains negated evidence;
- an appendix provides implementation parameters.

Assert the reranker prioritizes scope/qualifier match over generic semantic similarity.

- [ ] **Step 4: Implement deterministic reranking features**

```python
@dataclass(frozen=True, slots=True)
class RerankFeatures:
    lexical_rank: int | None
    vector_rank: int | None
    entity_coverage: float
    qualifier_coverage: float
    negation_compatibility: float
    section_prior: float
    evidence_type_prior: float
    exact_number_match: float
```

A model reranker may contribute one bounded score, but deterministic feature values and the final combination remain stored.

- [ ] **Step 5: Write failing exact-span tests**

Assert that span selection:

- returns the minimal contiguous substring that supports the proposition;
- includes enough context to interpret pronouns and comparative baselines;
- never crosses source-asset boundaries;
- validates quote equality and SHA-256;
- rejects a model-modified quote;
- preserves table/figure/algorithm coordinates when selected;
- returns `no_relevant_evidence` only after the complete-search condition is recorded.

- [ ] **Step 6: Implement exact span selector**

```python
class ExactSpanSelector:
    async def select(
        self,
        claim: CitingClaim,
        candidates: Sequence[RetrievedChunk],
        source_document: ParsedDocumentView,
        trace_id: str,
    ) -> SpanSelectionOutcome: ...
```

The model may propose offsets only within supplied candidate chunks. Re-read the canonical parsed text, derive the exact quote and call `validate_quote` before inserting `source_span`.

- [ ] **Step 7: Persist complete candidate history**

Store lexical/vector/entity scores, merged rank, reranker score/version, accepted/rejected status and reason codes. This history is required for Recall@K evaluation and post-incident analysis.

- [ ] **Step 8: Run retrieval decision tests**

Run:

```bash
cd starter/services/api
pytest tests/test_query_planner.py tests/test_evidence_reranker.py \
  tests/test_source_span_selector.py -v
pytest -q
```

Expected: qualifier-preserving ranking and exact quote integrity pass.

- [ ] **Step 9: Commit the evidence selection slice**

```bash
git add starter/services/api/src/citetrace_api/retrieval \
  starter/services/api/src/citetrace_api/db/repositories/evidence_candidates.py \
  starter/services/api/tests/test_query_planner.py \
  starter/services/api/tests/test_evidence_reranker.py \
  starter/services/api/tests/test_source_span_selector.py
git commit -m "feat: retrieve and validate exact source evidence"
```

### Task 5: Citation intent, relation and scope verification

**Files:**
- Create: `starter/services/api/src/citetrace_api/verification/__init__.py`
- Create: `starter/services/api/src/citetrace_api/verification/intents.py`
- Create: `starter/services/api/src/citetrace_api/verification/scope.py`
- Create: `starter/services/api/src/citetrace_api/verification/relations.py`
- Create: `starter/services/api/src/citetrace_api/verification/service.py`
- Create: `starter/services/api/tests/test_citation_intents.py`
- Create: `starter/services/api/tests/test_scope_comparison.py`
- Create: `starter/services/api/tests/test_relation_verifier.py`
- Create: `starter/services/api/tests/fixtures/evidence/relation-cases.jsonl`

**Interfaces:**
- Consumes: atomic claim, citation context, source access level and validated source spans.
- Produces: citation intents, one primary evidence relation, scope observations, reason codes, review recommendation and abstention.

- [ ] **Step 1: Write failing intent taxonomy tests**

Use fixture cases for background, definition, method adoption/extension, dataset, metric, benchmark, result support/contrast, limitation, future direction, software use and perfunctory mention. Assert output labels belong to `contracts/taxonomies/citation_intents.v1.yaml` and method adoption is not confused with result support.

- [ ] **Step 2: Implement citation intent classification**

Use `prompts/02_citation_intent.md`. Multi-label output is allowed, but every label carries one citing-context rationale and confidence. Empty labels require `review_required=true`.

- [ ] **Step 3: Write deterministic scope comparison tests**

```python
def test_two_languages_do_not_support_across_languages() -> None:
    result = compare_scope(
        citing={"population": "all languages"},
        source={"population": "English and German"},
    )
    assert result.compatibility == "mismatch"
    assert result.reason_code == "population_overgeneralized"
```

Add dataset, task, metric, time, modality, condition, quantity and certainty cases, including unknown values.

- [ ] **Step 4: Implement structured scope extraction/comparison**

Use deterministic values from claim qualifiers and source-span local context where available. A model may normalize free text to a dimension value but cannot drop the raw text or supporting span IDs.

- [ ] **Step 5: Write the relation decision-table tests**

Cover every relation label with positive and close-negative cases:

- same proposition and compatible qualifiers → `direct_support`;
- only one component supported → `partial_support`;
- premise/mechanism rather than direct result → `indirect_support`;
- incompatible result under comparable conditions → `contradicts`;
- claim expands beyond source → `overgeneralized`;
- non-comparable scopes → `scope_mismatch`;
- accessible complete search with no relevant evidence → `no_relevant_evidence`;
- relevant but inadequate spans → `insufficient_evidence`;
- no inspectable source → `inaccessible_source`.

- [ ] **Step 6: Implement relation verification through the gateway**

```python
class RelationVerificationService:
    async def verify(
        self,
        claim_id: UUID,
        source_span_ids: Sequence[UUID],
        trace_id: str,
    ) -> RelationDecision: ...
```

Use `prompts/05_relation_verifier.md`. Enforce postconditions:

- `inaccessible_source` requires `access_level=not_accessible` and zero source spans;
- support/contradiction/scope labels require at least one validated span;
- `no_relevant_evidence` requires a complete-search record;
- a quantitative direct-support label requires compatible metric, dataset, baseline and values;
- uncertain target association caps status at `review_required`.

- [ ] **Step 7: Run intent, scope and relation tests**

Run:

```bash
cd starter/services/api
pytest tests/test_citation_intents.py tests/test_scope_comparison.py \
  tests/test_relation_verifier.py -v
pytest -q
```

Expected: all taxonomy and decision-table cases pass.

- [ ] **Step 8: Commit scope-aware verification**

```bash
git add starter/services/api/src/citetrace_api/verification \
  starter/services/api/tests/test_citation_intents.py \
  starter/services/api/tests/test_scope_comparison.py \
  starter/services/api/tests/test_relation_verifier.py \
  starter/services/api/tests/fixtures/evidence/relation-cases.jsonl
git commit -m "feat: verify citation relations with scope"
```

### Task 6: Transformation analysis and confidence calibration

**Files:**
- Create: `starter/services/api/src/citetrace_api/verification/transformations.py`
- Create: `starter/services/api/src/citetrace_api/calibration/__init__.py`
- Create: `starter/services/api/src/citetrace_api/calibration/confidence.py`
- Create: `starter/services/api/src/citetrace_api/calibration/profiles.py`
- Create: `starter/services/api/tests/test_transformation_analyzer.py`
- Create: `starter/services/api/tests/test_confidence_vector.py`
- Create: `config/confidence-calibration.example.yaml`

**Interfaces:**
- Consumes: paired citing/source spans, method entities and stage quality features.
- Produces: evidence-backed transformation records, confidence vector, balanced/weakest-link scores and publication recommendation.

- [ ] **Step 1: Write failing paired-evidence transformation tests**

Test each closed transformation label and assert:

- `parameter_changed` includes source/citing values;
- `domain_transferred` names both domains;
- `extended`, `simplified` and `combined` identify the changed component;
- `adopted_unchanged` is rejected without affirmative paired evidence;
- `conceptual_inspiration` is not used as a generic fallback;
- empty transformations are valid when evidence is insufficient.

- [ ] **Step 2: Implement transformation analyzer**

Use `prompts/06_transformation_analyzer.md`. Every returned record requires allowed source and citing span IDs. Persist changed dimensions and model execution provenance.

- [ ] **Step 3: Define confidence features and vector**

```python
@dataclass(frozen=True, slots=True)
class ConfidenceVector:
    parse: float
    reference_resolution: float
    source_access: float
    evidence_retrieval: float
    relation_verification: float
    explanation_grounding: float
    weakest_link: float
    balanced_score: float
    calibration_profile: str
    reasons: tuple[ConfidenceReason, ...]
```

- [ ] **Step 4: Add calibration configuration**

```yaml
version: 1.0.0
profiles:
  default-v1:
    verified_minimum_weakest_link: 0.82
    verified_minimum_balanced_score: 0.86
    limited_minimum_weakest_link: 0.55
    review_when_target_association_uncertain: true
    review_when_version_uncertain: true
    block_when_quote_invalid: true
    balanced_weights:
      parse: 0.10
      reference_resolution: 0.18
      source_access: 0.08
      evidence_retrieval: 0.22
      relation_verification: 0.30
      explanation_grounding: 0.12
```

- [ ] **Step 5: Write failing confidence/status tests**

Assert that:

- one stage at 0.40 prevents `verified` even when others are 0.99;
- inaccessible source maps to `limited` or `blocked` with an abstention, never `verified`;
- invalid quote forces `blocked`;
- version uncertainty forces `review_required` under the profile;
- confidence reasons name low stages and contributing reason codes;
- one unexplained scalar is never returned.

- [ ] **Step 6: Implement calibrated publication recommendation**

Use held-out calibration artifacts to fit monotonic mappings from raw stage features to calibrated probabilities. Runtime loads a signed profile artifact and calculates weighted geometric mean plus weakest link. Do not train calibration on the hidden release test split.

- [ ] **Step 7: Run transformation and calibration tests**

Run:

```bash
cd starter/services/api
pytest tests/test_transformation_analyzer.py tests/test_confidence_vector.py -v
pytest -q
```

Expected: paired evidence and stage-capped status decisions pass.

- [ ] **Step 8: Commit transformation and confidence logic**

```bash
git add config/confidence-calibration.example.yaml \
  starter/services/api/src/citetrace_api/verification/transformations.py \
  starter/services/api/src/citetrace_api/calibration \
  starter/services/api/tests/test_transformation_analyzer.py \
  starter/services/api/tests/test_confidence_vector.py
git commit -m "feat: analyze transformations and calibrate confidence"
```

### Task 7: Grounded explanations and blocking quality audit

**Files:**
- Create: `starter/services/api/src/citetrace_api/explanations/__init__.py`
- Create: `starter/services/api/src/citetrace_api/explanations/models.py`
- Create: `starter/services/api/src/citetrace_api/explanations/generator.py`
- Create: `starter/services/api/src/citetrace_api/audit/__init__.py`
- Create: `starter/services/api/src/citetrace_api/audit/checks.py`
- Create: `starter/services/api/src/citetrace_api/audit/service.py`
- Create: `starter/services/api/src/citetrace_api/db/repositories/evidence_links.py`
- Create: `starter/services/api/tests/test_relationship_summary.py`
- Create: `starter/services/api/tests/test_quality_auditor.py`
- Create: `starter/services/api/tests/test_evidence_link_repository.py`

**Interfaces:**
- Consumes: verified claim, source spans, relation, scope, transformation, limitations and confidence vector.
- Produces: statement-level grounded explanations, immutable evidence link, audit decision and publishable status.

- [ ] **Step 1: Write failing statement-grounding tests**

Assert that:

- an `evidence_based` statement requires at least one supporting source span;
- an `inference` states that it is an inference and lists supporting records;
- limitation text preserves version/access/coverage uncertainty;
- generated quotes must match already approved source-span quote values;
- beginner analogies are labeled and are not counted as scientific evidence;
- implementation mode prioritizes components/settings/missing details;
- review mode prioritizes mismatch and uncertainty.

- [ ] **Step 2: Implement explanation models and generator**

```python
@dataclass(frozen=True, slots=True)
class ExplanationStatementDraft:
    kind: ExplanationStatementKind
    text: str
    supporting_citing_span_ids: tuple[UUID, ...]
    supporting_source_span_ids: tuple[UUID, ...]
    supporting_record_ids: tuple[UUID, ...]


class RelationshipSummaryGenerator:
    async def generate(self, evidence: VerifiedEvidenceBundle, audience: Audience, mode: AnalysisMode) -> ExplanationDraft: ...
```

Use `prompts/07_relationship_summary.md` and `prompts/08_beginner_explainer.md`. Validate all IDs and sentence support before persistence.

- [ ] **Step 3: Write failing deterministic audit tests**

Test blocking conditions:

- exact quote mismatch,
- offset outside asset,
- support relation without source span,
- material statement without support/inference marker,
- access disclosure more permissive than source asset,
- invalid public schema,
- prompt-injection leakage,
- generator and auditor execution are the same when policy forbids it.

Test passing limited outcomes for inaccessible and abstract-only sources with explicit limitations.

- [ ] **Step 4: Implement deterministic audit checks first**

```python
class AuditCheck(Protocol):
    id: str
    async def run(self, bundle: EvidencePublicationBundle) -> AuditCheckResult: ...
```

Required checks include `quote_exact_match`, `offset_valid`, `relation_has_evidence`, `statement_grounding`, `access_disclosure`, `schema_valid`, `artifact_id_containment`, `prompt_injection_resistance` and `auditor_independence`.

- [ ] **Step 5: Implement independent model audit**

After deterministic checks pass, invoke `prompts/09_quality_auditor.md` through an allowed auditor route different from the generator. The model may downgrade or request review but cannot override a deterministic failure.

- [ ] **Step 6: Write failing atomic-publication repository tests**

Assert that evidence link, source-span associations, explanation statements and audit decision commit together. A blocked audit stores the candidate records for debugging but excludes the link from public list queries.

- [ ] **Step 7: Implement evidence-link publication transaction**

```python
class EvidenceLinkRepository:
    async def publish(self, command: PublishEvidenceLink) -> UUID: ...
    async def get_public(self, evidence_link_id: UUID) -> EvidenceLinkView | None: ...
```

Persist taxonomy versions, model execution IDs, confidence profile, source access, abstention and audit status. Validate the resulting public object against `contracts/schemas/evidence-link.v1.schema.json` before commit.

- [ ] **Step 8: Run explanation/audit/repository tests**

Run:

```bash
cd starter/services/api
pytest tests/test_relationship_summary.py tests/test_quality_auditor.py \
  tests/test_evidence_link_repository.py -v
pytest -q
```

Expected: unsupported statements and invalid quotes are blocked, while correctly limited outcomes publish safely.

- [ ] **Step 9: Commit evidence publication**

```bash
git add starter/services/api/src/citetrace_api/explanations \
  starter/services/api/src/citetrace_api/audit \
  starter/services/api/src/citetrace_api/db/repositories/evidence_links.py \
  starter/services/api/tests/test_relationship_summary.py \
  starter/services/api/tests/test_quality_auditor.py \
  starter/services/api/tests/test_evidence_link_repository.py
git commit -m "feat: publish audited grounded evidence links"
```

### Task 8: Mode-aware reading priority and section recommendation

**Files:**
- Create: `starter/services/api/src/citetrace_api/prioritization/__init__.py`
- Create: `starter/services/api/src/citetrace_api/prioritization/models.py`
- Create: `starter/services/api/src/citetrace_api/prioritization/features.py`
- Create: `starter/services/api/src/citetrace_api/prioritization/service.py`
- Create: `starter/services/api/src/citetrace_api/db/repositories/reference_priorities.py`
- Create: `starter/services/api/tests/test_reading_priority.py`
- Create: `starter/services/api/tests/test_reference_priority_repository.py`
- Modify: `contracts/db/schema.sql`
- Modify: `contracts/openapi.yaml`

**Interfaces:**
- Consumes: analysis mode, reference resolution, citation intents, evidence-link outcomes, source access, citation frequency/section distribution, transformation roles and cited-work section map.
- Produces: `ReadingPriority` with a mode-relative score/band, stable reason codes, recommended source sections and access-aware next action. It is not a paper-quality, prestige or truth score.

- [ ] **Step 1: Write failing mode-policy tests**

Create fixtures where the same references receive different priorities by mode. Assert:

- `understand` favors foundational concepts and methods needed to follow the current paper;
- `implement` favors adopted methods, datasets, metrics, settings, algorithms and appendices;
- `review` favors ambiguous resolutions, scope mismatch, contradiction, overgeneralization and weak evidence;
- `survey` favors lineage roots, representative branches and contrasting results;
- `present` favors references necessary to explain motivation, novelty and one defensible result;
- citation count or venue prestige alone cannot produce `must_read`;
- inaccessible but structurally important work remains high priority with an access limitation and recovery action.

- [ ] **Step 2: Define the typed priority contract**

```python
class ReadingPriorityBand(StrEnum):
    MUST_READ = "must_read"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class ReadingPriority:
    analysis_id: UUID
    reference_entry_id: UUID
    mode: AnalysisMode
    score: float
    band: ReadingPriorityBand
    reason_codes: tuple[str, ...]
    recommended_sections: tuple[str, ...]
    next_actions: tuple[str, ...]
    feature_profile_version: str
```

Require `0 <= score <= 1`, at least one reason code, and an explicit feature profile version.

- [ ] **Step 3: Write failing deterministic feature tests**

Test independent features for method dependency, dataset/metric dependency, repeated use across sections, lineage centrality inside the analyzed subgraph, relation risk, implementation relevance, source availability, version uncertainty and redundancy with already selected references. Test that every feature is derivable from stored artifacts and that no provider citation-count field is silently treated as scientific importance.

- [ ] **Step 4: Implement deterministic scoring and band policy**

```python
class ReadingPriorityService:
    def rank(
        self,
        mode: AnalysisMode,
        references: Sequence[ReferencePriorityInput],
        profile: PriorityProfile,
    ) -> tuple[ReadingPriority, ...]: ...
```

Use a versioned weighted feature profile plus deterministic tie-breaking by reference-entry UUID. Cap the band when reference identity is unresolved; preserve high structural importance while disclosing inaccessible source status. Generate recommended sections only from verified source structure or provider section metadata marked with its access level.

- [ ] **Step 5: Write failing persistence and read-contract tests**

Assert one current priority record per analysis/reference/mode/profile, immutable supersession on profile changes, workspace isolation, stable ordering, reason-code retention, and OpenAPI serialization. Confirm that evidence updates trigger recomputation without mutating historical priority records.

- [ ] **Step 6: Implement repository and read model**

```python
class ReferencePriorityRepository:
    async def append_many(self, priorities: Sequence[ReadingPriority]) -> None: ...
    async def list_current(
        self, analysis_id: UUID, mode: AnalysisMode
    ) -> tuple[ReadingPriority, ...]: ...
```

Add the normalized table, indexes and RLS policy to `contracts/db/schema.sql`; add priority fields/filter semantics to `contracts/openapi.yaml` and the reader reference-map contract.

- [ ] **Step 7: Run priority tests and contract checks**

Run:

```bash
python scripts/validate_package.py
cd starter/services/api
pytest tests/test_reading_priority.py tests/test_reference_priority_repository.py -v
pytest -q
```

Expected: mode-relative rankings, deterministic reasons, tenant isolation and schema serialization pass.

- [ ] **Step 8: Commit mode-aware prioritization**

```bash
git add contracts/db/schema.sql contracts/openapi.yaml \
  starter/services/api/src/citetrace_api/prioritization \
  starter/services/api/src/citetrace_api/db/repositories/reference_priorities.py \
  starter/services/api/tests/test_reading_priority.py \
  starter/services/api/tests/test_reference_priority_repository.py
git commit -m "feat: rank references by mode-aware reading priority"
```

### Task 9: End-to-end analysis worker and evaluation adapter

**Files:**
- Create: `starter/services/api/src/citetrace_api/orchestration/evidence_handlers.py`
- Create: `starter/services/api/src/citetrace_api/evaluation/__init__.py`
- Create: `starter/services/api/src/citetrace_api/evaluation/export.py`
- Create: `starter/services/api/tests/test_evidence_pipeline.py`
- Create: `starter/services/api/tests/test_evaluation_export.py`
- Modify: `starter/services/api/src/citetrace_api/orchestration/handlers.py`
- Modify: `contracts/event_catalog.yaml`

**Interfaces:**
- Consumes: `analysis.references.ready` and in-scope claim/reference/source artifacts.
- Produces: audited evidence links for every claim-target case, durable progress, terminal analysis state and anonymized evaluation export.

- [ ] **Step 1: Write a failing mixed-outcome pipeline test**

```python
@pytest.mark.anyio
async def test_pipeline_completes_with_verified_limited_and_review_cases(
    evidence_pipeline: EvidencePipeline,
) -> None:
    outcome = await evidence_pipeline.run(ANALYSIS_ID, trace_id="trace-evidence-1")
    assert outcome.total_cases == 4
    assert outcome.verified == 2
    assert outcome.limited == 1
    assert outcome.review_required == 1
    assert outcome.blocked == 0
    assert outcome.analysis_status == "completed_with_limits"
```

Add crash/retry tests at claim extraction, retrieval, verification, explanation and audit boundaries.

- [ ] **Step 2: Implement per-case idempotent orchestration**

Fingerprint every stage from immutable input artifact hashes and version IDs. A successful stage is reused on redelivery; a new prompt/model/parser version creates a new stage attempt without deleting the old result.

- [ ] **Step 3: Implement terminal status aggregation**

Rules:

- `completed` when all in-scope cases are verified and no material limitation exists;
- `completed_with_limits` when at least one case is limited or review-required and no blocking infrastructure failure prevents useful output;
- `failed` when the citing document cannot be parsed or no in-scope case can produce a safe outcome;
- `cancelled` only on user/system cancellation.

- [ ] **Step 4: Write failing evaluation export tests**

Assert that export contains case IDs, artifact IDs, labels, scores and reason codes but excludes source bytes, private quotes unless explicitly authorized, user identity and provider secrets.

- [ ] **Step 5: Implement evaluation export**

```python
class EvaluationExporter:
    async def export_analysis(self, analysis_id: UUID, policy: ExportPolicy) -> list[EvaluationCaseRecord]: ...
```

Use stable pseudonymous IDs and record exact schema/taxonomy/prompt/model/calibration versions.

- [ ] **Step 6: Update event catalog**

Add stage events for claims extracted, evidence candidates retrieved, relations verified, explanations audited and analysis completed. Event payloads contain artifact IDs and counts, not raw paper content.

- [ ] **Step 7: Run end-to-end engine tests**

Run:

```bash
python scripts/validate_package.py
cd starter/services/api
pytest tests/test_evidence_pipeline.py tests/test_evaluation_export.py -v
pytest -q
```

Expected: retries are idempotent and mixed safe outcomes complete with accurate counts.

- [ ] **Step 8: Commit the evidence engine vertical slice**

```bash
git add contracts/event_catalog.yaml \
  starter/services/api/src/citetrace_api/orchestration/evidence_handlers.py \
  starter/services/api/src/citetrace_api/orchestration/handlers.py \
  starter/services/api/src/citetrace_api/evaluation \
  starter/services/api/tests/test_evidence_pipeline.py \
  starter/services/api/tests/test_evaluation_export.py
git commit -m "feat: complete audited evidence analysis pipeline"
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
python scripts/score_sample_predictions.py --gold eval/sample_cases.jsonl \
  --predictions eval/sample_predictions.jsonl
```

Accept the plan only when:

- every source quote matches immutable asset text and offsets;
- multi-reference clusters are judged per target;
- all closed taxonomy labels match contracts and database enums;
- every relation has the required evidence or correct abstention;
- stage confidence and reason codes are visible and status is capped by weak stages;
- no unsupported material explanation sentence is publishable;
- reading priority is mode-relative, reason-coded and never presented as paper quality;
- generator and final auditor executions satisfy independence policy;
- pipeline retries do not duplicate source spans, evidence links or model side effects;
- all tests, contract validation and synthetic evaluation checks pass.
