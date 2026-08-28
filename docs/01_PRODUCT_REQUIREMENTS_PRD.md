# CiteTrace Product Requirements Document

> **Version:** 1.0.0  
> **Date:** 2026-08-28  
> **Owner:** Product/domain lead  
> **Depends on:** `00_MASTER_BLUEPRINT.md`

---

## 1. Product objective

CiteTrace must reduce the work required to understand and verify citations in scientific papers while increasing, rather than reducing, the user's ability to inspect original sources.

The product is successful when a user can answer, in one evidence-centered workflow:

- what the citing paper claims,
- which source it cites,
- what source material is actually relevant,
- whether the citation supports the claim at the claimed scope,
- what changed between the source and the citing paper,
- how much of that conclusion is verified versus uncertain.

---

## 2. Personas

### Persona P1 — 학부 연구생 민지

- 논문 독해 경험이 적다.
- Related Work의 레퍼런스가 왜 중요한지 구분하지 못한다.
- 수식과 방법론을 쉬운 설명으로 연결해 주길 원한다.
- 잘못된 AI 설명을 그대로 믿을 위험이 높다.

**Success:** 핵심 레퍼런스 5개와 각 역할을 파악하고 발표 자료를 근거와 함께 만든다.

### Persona P2 — 석사과정 현우

- 모델 재현을 위해 method, dataset, metric 원 논문을 추적한다.
- arXiv와 학회 버전 차이, 누락된 하이퍼파라미터 때문에 시간을 쓴다.
- 구현에 필요한 구간만 빠르게 읽고 싶다.

**Success:** 현재 방법의 의존성, 변경점, 공식 코드·데이터셋 출처를 구조화된 체크리스트로 얻는다.

### Persona P3 — 박사과정·리뷰어 서연

- 과장된 related-work 주장과 부적절한 인용을 찾는다.
- 각 판정의 원문 근거와 불확실성을 요구한다.
- 자동 판정이 아니라 우선 검토할 항목을 원한다.

**Success:** 위험도가 높은 인용을 우선 검토하고, 원문 근거를 직접 열어 판단한다.

### Persona P4 — 기업 R&D 분석가 준호

- 기술 동향과 아이디어 계보를 빠르게 정리한다.
- 내부 문서와 공개 논문을 함께 다루되 정보 유출을 허용할 수 없다.
- 분석 결과를 팀과 공유하고 감사할 수 있어야 한다.

**Success:** private workspace에서 출처가 명확한 기술 계보를 만들고 공유한다.

---

## 3. Primary user journeys

### Journey J1 — 인용 하나 즉시 확인

1. 사용자가 PDF를 업로드한다.
2. 시스템이 지원 가능성·보안·접근 정책을 검사한다.
3. 첫 페이지와 구조화 텍스트를 빠르게 표시한다.
4. 인용 anchor가 클릭 가능한 상태가 된다.
5. 사용자가 `[12]`를 클릭한다.
6. 시스템은 우선 해당 레퍼런스 identity와 source availability를 보여준다.
7. 분석 완료 후 current claim, evidence span, relation, transformation, confidence를 표시한다.
8. 사용자는 source span을 PDF에서 연다.
9. 결과에 피드백을 남기거나 저장한다.

**Critical acceptance:** source span을 확보하지 못한 경우 관계를 확정적으로 표현하지 않는다.

### Journey J2 — 전체 논문 핵심 레퍼런스 파악

1. 사용자가 `Understand` 모드를 선택한다.
2. 시스템이 인용별 역할과 핵심성을 계산한다.
3. 핵심 기반, 방법 의존, 데이터셋, 평가, 배경 인용으로 그룹화한다.
4. 상위 5–10개의 읽기 우선순위를 제공한다.
5. 사용자가 그룹 또는 lineage graph에서 탐색한다.
6. 저장한 reading queue를 내보낸다.

### Journey J3 — 구현 재현

1. 사용자가 `Implement` 모드를 선택한다.
2. 시스템이 method adoption/extension, dataset use, metric use, tool use 인용을 우선한다.
3. 각 관계에서 “그대로 사용 / 변경 / 누락 가능성”을 정리한다.
4. source code, dataset page, appendix 등 확인 가능한 자원을 연결한다.
5. 재현 checklist를 생성하되 확인되지 않은 값은 미확인으로 표시한다.

### Journey J4 — 리뷰 위험 항목 점검

1. 사용자가 `Review` 모드를 선택한다.
2. 시스템은 `overgeneralized`, `scope_mismatch`, `contradicts`, `no_relevant_evidence`, low confidence를 우선 정렬한다.
3. 사용자는 paired view로 citing claim과 source evidence를 확인한다.
4. 판정을 수정하고 private review note를 작성한다.
5. 제품은 사람의 최종 verdict를 대신 내리지 않는다.

### Journey J5 — 소스 미접근

1. reference identity는 확인되지만 full text가 없다.
2. 시스템은 합법적 OA 위치와 사용자가 업로드할 수 있는 옵션을 탐색한다.
3. 초록만 확보되면 `abstract_only`를 명확히 표시한다.
4. 전문이 필요한 판정은 `inaccessible_source` 또는 `insufficient_evidence`가 된다.
5. 사용자가 source PDF를 추가하면 동일 분석이 versioned rerun으로 이어진다.

---

## 4. Functional requirements

### FR-100 Document ingestion

| ID | Requirement | Acceptance |
|---|---|---|
| FR-101 | PDF upload and supported scholarly URL intake | immutable asset ID and checksum created |
| FR-102 | MIME, magic bytes, size, pages, encryption and malware policy checks | rejected file returns typed reason; no parser call |
| FR-103 | Workspace ownership and retention policy recorded | asset cannot be read outside workspace |
| FR-104 | Duplicate upload detection within policy boundary | duplicate reuses permitted asset; private assets never cross tenant |
| FR-105 | Cancellation | queued/running job moves to cancellation path and stops new fan-out |

### FR-200 Structured parsing

| ID | Requirement | Acceptance |
|---|---|---|
| FR-201 | Extract sections, paragraphs, sentences, bibliography and citation anchors | every anchor references a parsed bibliography item or unresolved state |
| FR-202 | Preserve page and bounding coordinates where available | UI can open/highlight source region |
| FR-203 | Support numeric and author–year citation styles | regression fixtures cover both |
| FR-204 | Detect multi-citation clusters | each target is represented separately with shared context |
| FR-205 | Produce document quality grade | grade includes reasons and enabled/disabled features |

### FR-300 Reference resolution

| ID | Requirement | Acceptance |
|---|---|---|
| FR-301 | Normalize DOI, arXiv, PMID and title/author/year metadata | normalized identifiers are canonical-form validated |
| FR-302 | Query multiple provider adapters | provider provenance and timestamps retained |
| FR-303 | Score and rank candidates | feature-level score explanation stored |
| FR-304 | Preserve version relationships | selected work and selected source version are distinct fields |
| FR-305 | Abstain on ambiguity | no arbitrary top candidate below configured margin/threshold |
| FR-306 | Allow user correction | correction creates immutable event and rerun target |

### FR-400 Source acquisition

| ID | Requirement | Acceptance |
|---|---|---|
| FR-401 | Prefer user-authorized or lawful OA full text | acquisition path and license/access level recorded |
| FR-402 | Fall back to abstract or metadata | UI and API expose limitation |
| FR-403 | Prevent paywall bypass | blocked paths are tested and audited |
| FR-404 | Version source assets by content checksum | analysis never silently switches source bytes |
| FR-405 | Quarantine risky remote content | remote asset passes same ingest gates as upload |

### FR-500 Citation context and claim extraction

| ID | Requirement | Acceptance |
|---|---|---|
| FR-501 | Build context window around citation | includes sentence and configurable neighboring sentences/section heading |
| FR-502 | Decompose context into atomic claims | each claim has exact span and citation target association |
| FR-503 | Support citation clusters | claim-to-target association may be one-to-many and uncertain |
| FR-504 | Preserve qualifiers | negation, hedging, population, metric, time and conditions retained |

### FR-600 Evidence retrieval

| ID | Requirement | Acceptance |
|---|---|---|
| FR-601 | Section-aware source chunking | chunks preserve heading, page, paragraph and coordinate provenance |
| FR-602 | Hybrid lexical/vector retrieval | candidate features stored; offline fixtures deterministic |
| FR-603 | Cross-encoder or verifier reranking | top candidates include rerank score and model version |
| FR-604 | Search text, captions and structured table/figure descriptors | evidence type explicitly represented |
| FR-605 | Exact span extraction and validation | displayed quote is exact substring of normalized source asset |
| FR-606 | Counterevidence search for strong claims | relation verifier receives supporting and contrasting candidates |

### FR-700 Analysis

| ID | Requirement | Acceptance |
|---|---|---|
| FR-701 | Multi-label citation intent classification | output conforms to taxonomy version |
| FR-702 | Evidence relation classification | label plus scope dimensions and rationale span |
| FR-703 | Transformation/lineage classification | output only when paired evidence supports it |
| FR-704 | Stage-level confidence vector | every published card includes populated vector or explicit unavailable value |
| FR-705 | Policy-driven abstention | threshold and reasons stored and user-visible |
| FR-706 | Analyze reference importance for selected mode | score is mode-relative, not paper-quality score |

### FR-800 Explanation and learning

| ID | Requirement | Acceptance |
|---|---|---|
| FR-801 | Relationship-centered cited-paper summary | summary explicitly says why source matters here |
| FR-802 | Beginner explanation | terminology is expanded and prerequisites listed |
| FR-803 | Expert explanation | concise, technical, paired comparison available |
| FR-804 | No unsupported statement | each material statement maps to source or marked inference |
| FR-805 | Reading recommendation | priority and recommended sections explained |

### FR-900 Reader and graph

| ID | Requirement | Acceptance |
|---|---|---|
| FR-901 | Clickable in-text citations | keyboard and pointer accessible |
| FR-902 | Evidence card | all ten core blocks from blueprint represented |
| FR-903 | Open exact source region | page/section/span navigation works where coordinates exist |
| FR-904 | Analysis progress and partial availability | stages stream without claiming unfinished work complete |
| FR-905 | Reference list filters and grouping | intent, relation, importance, access and confidence filters |
| FR-906 | Lineage graph | edge type and evidence are inspectable; decorative graph is not enough |

### FR-1000 Feedback and collaboration

| ID | Requirement | Acceptance |
|---|---|---|
| FR-1001 | Structured feedback categories | identity, evidence, relation, transformation, explanation, access |
| FR-1002 | Correction details | corrected target/span/label retained with actor and timestamp |
| FR-1003 | Private notes | tenant and role controls enforced |
| FR-1004 | Export | provenance-preserving JSON/Markdown export |
| FR-1005 | Share | shared view respects source licenses and workspace policy |

### FR-1100 Operations

| ID | Requirement | Acceptance |
|---|---|---|
| FR-1101 | Idempotent jobs | repeated idempotency key returns same logical job |
| FR-1102 | Resumable stages | completed checkpoints survive worker restart |
| FR-1103 | Provider degradation | partial analysis continues with visible limitation |
| FR-1104 | Audit | source acquisition, access, model runs and user corrections logged |
| FR-1105 | Deletion | user revokes access immediately and receives deletion status |

---

## 5. Non-functional requirements

### NFR-1 Trustworthiness

- zero fabricated displayed quotes in blocking evaluation
- no relation judgment without retrievable evidence record
- no hidden abstract-only inference presented as full-text verification
- all user-visible uncertainty reasons localizable and understandable

### NFR-2 Security and privacy

- tenant isolation at API, database and object-storage layers
- private assets excluded from shared model training by default
- secrets never present in model prompts
- document text excluded from default application logs
- remote URL fetch protected against SSRF

### NFR-3 Performance

- API reads for completed evidence cards p95 under 500 ms in target environment
- first document shell visible before full analysis completion
- priority citation can be analyzed independently of whole-paper fan-out
- analysis queues enforce workspace and global concurrency budgets

### NFR-4 Reliability

- job transitions durable and idempotent
- every external call has timeout, retry policy, rate limit handling and circuit breaker
- model/schema failure becomes typed state, not corrupt output
- work can resume from latest valid checkpoint

### NFR-5 Accessibility

- WCAG 2.2 AA target
- citation anchors and evidence cards keyboard navigable
- relation and confidence never conveyed only by color
- PDF and structured-text alternatives available
- focus remains stable during progress updates

### NFR-6 Maintainability

- provider and model adapters behind typed interfaces
- versioned prompts, schemas and taxonomies
- contract tests for external/public boundaries
- no microservice split without ADR and measured need

---

## 6. User-visible states and copy rules

| Internal state | User message principle |
|---|---|
| `ambiguous_reference` | “비슷한 논문 후보가 여러 개라 자동 확정하지 않았습니다.” |
| `inaccessible_source` | “논문 정체는 확인했지만 검증 가능한 원문을 확보하지 못했습니다.” |
| `abstract_only` | “아래 판단은 초록 범위에서만 확인했습니다.” |
| `insufficient_evidence` | “현재 주장과 직접 연결되는 원문 근거를 찾지 못했습니다.” |
| `scope_mismatch` | “관련 결과는 있지만 데이터·조건·대상 범위가 현재 주장과 다릅니다.” |
| `review_required` | “후보들이 비슷해 사람 확인이 필요합니다.” |
| `unsupported_document` | “이 문서는 현재 지원 범위를 벗어나 정확한 인용 연결을 보장하기 어렵습니다.” |

Copy must never imply that absence of found evidence proves falsity.

---

## 7. Prioritization

### Must — credible core

- secure upload
- structured parsing and citation linking
- reference resolution with abstention
- user-provided or lawful OA source acquisition
- evidence retrieval and exact quote validation
- evidence card with provenance and confidence
- structured feedback
- test and evaluation harness

### Should — strong product

- intent/relation/transformation labels
- whole-paper priority and modes
- lineage graph
- beginner/expert explanations
- export and shared workspace

### Later — expansion

- multilingual and scanned documents
- broad table reasoning
- recursive graph beyond controlled depth
- browser extension and authoring integrations
- institution-wide search and private corpus graph

---

## 8. Product acceptance scenarios

### Scenario A — Direct method adoption

Given a citing sentence explicitly states that it uses a method from reference `[12]`, and the cited full text contains the method definition, when analysis completes, then the card:

- resolves the correct work/version,
- displays the exact method span,
- labels `method_adoption`,
- labels relation at least `direct_support` or `partial_support` according to scope,
- labels `adopted_unchanged` only if paired evidence shows no stated change,
- exposes source and confidence provenance.

### Scenario B — Overgeneralized empirical result

Given a citing claim says a method works “across domains,” while the cited paper reports only one dataset and task, then the card:

- retrieves the reported experiment,
- records domain/task scope,
- labels `overgeneralized` or `scope_mismatch`,
- explains the exact difference without claiming research misconduct.

### Scenario C — Inaccessible full text

Given the source identity is high-confidence but only metadata/abstract is lawfully available, then the card:

- shows `abstract_only` or `inaccessible_source`,
- does not quote unavailable full text,
- does not emit a definitive transformation judgment,
- offers a user-authorized source upload path.

### Scenario D — Wrong reference candidate

Given two works share a nearly identical title, when provider candidates are close and author/year features conflict, then the system:

- returns `ambiguous_reference`,
- shows candidates and distinguishing attributes,
- requires a user or higher-confidence identifier before full analysis.

### Scenario E — Prompt injection in paper

Given source text contains instructions to ignore system policy or expose secrets, then the system:

- treats the text as evidence only,
- performs no requested tool or network action,
- records no secret or system prompt in output,
- completes or abstains according to scholarly evidence.

---

## 9. Analytics events

- `document_ingest_started`
- `document_ingest_rejected`
- `analysis_created`
- `analysis_stage_completed`
- `citation_opened`
- `source_evidence_opened`
- `reference_saved`
- `feedback_submitted`
- `analysis_abstained`
- `source_upload_requested`
- `export_created`
- `workspace_share_created`

Analytics must use pseudonymous IDs and avoid raw paper text.

---

## 10. Exit criteria for product beta

- Must requirements implemented and contract-tested
- critical security threat tests pass
- 300+ adjudicated gold cases available, with minimum slice sizes defined in evaluation spec
- quality targets met or explicitly narrowed by supported-domain gate
- no fabricated quote in blocking suite
- private deletion and access revocation verified
- support documentation explains limitations and source policy
- user study demonstrates users can correctly interpret relation and uncertainty displays
