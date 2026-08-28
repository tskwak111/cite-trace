# CiteTrace Product and System Design Specification

> **Approval basis:** 2026-08-28 대화에서 사용자가 승인한 제품 방향 — 현재 논문의 인용문과 레퍼런스 원문의 근거를 연결하고, 지지·반박·범위 차이와 계승·변형을 검증 가능한 형태로 설명하는 에이전트.
>
> **Normative source:** 이 문서는 구현 범위와 시스템 경계를 고정하는 상위 설계 계약이다. 세부 요구사항과 기계 계약은 아래의 문서·OpenAPI·JSON Schema·DB schema를 단일 원본으로 사용하며, 이 문서에 내용을 복제하지 않는다.

## 1. Product contract

CiteTrace는 일반적인 논문 검색기, PDF 챗봇, 초록 요약기 또는 인용 그래프 뷰어가 아니다. 사용자가 읽는 논문의 **원자적 주장과 인용 대상의 정확한 원문 근거 사이에 검증 가능한 링크를 만드는 citation intelligence system**이다.

사용자가 인용 표식을 선택하면 시스템은 다음 질문에 답해야 한다.

1. 이 위치에서 왜 해당 자료를 인용했는가?
2. 인용 대상의 어느 버전·페이지·섹션·문장·표·그림·수식·알고리즘이 관련 근거인가?
3. 그 근거가 현재 주장을 직접 지지하는가, 일부만 지지하는가, 간접적 근거인가, 반박하는가, 범위가 다른가, 또는 판단할 수 없는가?
4. 현재 논문은 선행연구에서 무엇을 채택하고 무엇을 변경·확장·단순화·이식했는가?
5. 사용자가 결과를 믿기 전에 어떤 원문과 제한사항을 확인해야 하는가?

모든 사용자 노출 결과는 정확한 원문 span, 버전·접근 수준, 단계별 provenance와 confidence 또는 명시적 abstention으로 되돌아갈 수 있어야 한다.

## 2. Success definition

제품 성공은 답변의 유창함이나 길이가 아니라 다음 결과로 판단한다.

- 사용자가 핵심 레퍼런스와 읽기 순서를 빠르게 찾는다.
- 원문 근거를 한 번의 조작으로 확인한다.
- 인용 관계의 지지·반박·범위·변형 판정을 사람이 재검증할 수 있다.
- 접근할 수 없는 자료와 불충분한 근거를 시스템이 숨기지 않는다.
- 생성된 설명의 모든 중요한 문장이 source/citing span으로 연결된다.
- 초보자는 선수 개념과 연구 계보를 이해하고, 연구자는 원문 검증 시간을 줄인다.

정량 목표와 릴리스 차단 기준은 `docs/09_EVALUATION_GOLDSET_QA.md`와 `eval/rubric.yaml`이 정본이다.

## 3. Initial release scope

초기 릴리스는 born-digital scientific PDF와 DOI/arXiv 기반 입력을 대상으로 한다. 핵심 경로는 다음으로 제한한다.

1. 논문 업로드 또는 식별자 입력
2. 안전한 문서 검증과 구조 파싱
3. 본문 인용 anchor와 bibliography entry 연결
4. 레퍼런스의 work/version 식별
5. 합법적인 원문·초록·메타데이터 확보와 접근 수준 기록
6. 인용 문맥에서 원자적 주장과 qualifier 추출
7. 인용 대상별 hybrid retrieval과 exact span 생성
8. 관계·범위·변형 판정과 독립 감사
9. 세 단계 reader에서 결과·근거·제한사항 표시
10. 사용자 피드백과 재현 가능한 provenance 보존

초기 릴리스에서 OCR 중심 스캔 문서, 모든 수식·표의 완전한 의미 복원, 무제한 재귀 문헌 계보, 자동 논문 작성, 완전한 systematic review 자동화, 유료벽 우회는 범위 밖이다.

## 4. Architecture

초기 시스템은 **modular monolith API + asynchronous workers + PostgreSQL/pgvector + immutable object assets**로 구성한다. 제품 경계가 안정되기 전 마이크로서비스 분해를 피하되, ingestion, resolution, acquisition, evidence, explanation, evaluation, workspace 모듈의 인터페이스는 명확히 분리한다.

핵심 흐름은 다음과 같다.

```text
Upload/Identifier
  → validation and immutable asset registration
  → structural parsing and citation-anchor linking
  → reference work/version resolution
  → lawful source discovery and acquisition
  → atomic claim extraction and qualifier preservation
  → hybrid candidate retrieval and reranking
  → exact quote/offset/hash validation
  → relation, scope and transformation verification
  → grounded explanation generation
  → independent audit and publication status
  → three-pane reader, feedback and export
```

판단 모델은 URL을 선택하거나 원문을 직접 가져오지 않는다. source acquisition은 별도의 정책·SSRF 검증 계층이 수행하며, 모델은 시스템이 제공한 닫힌 candidate와 taxonomy 안에서만 판단한다.

세부 런타임, 데이터 흐름, 배포 토폴로지는 `docs/04_SYSTEM_ARCHITECTURE.md`와 ADR이 정본이다.

## 5. Evidence-first invariant

시스템은 설명을 먼저 만들고 나중에 근거를 붙이지 않는다. 다음 순서를 강제한다.

```text
source/version identity
→ candidate retrieval
→ exact span validation
→ relation/scope/transformation judgment
→ statement-level grounded explanation
→ independent audit
→ publication
```

다음 조건을 만족하지 못하면 결과는 `review_required`, `limited` 또는 `blocked` 상태여야 한다.

- quote가 immutable normalized asset의 exact offset과 일치하지 않는다.
- 인용 대상 work/version 식별에 실질적 충돌이 있다.
- full-text가 없는데 full-text 수준의 판정을 요구한다.
- support 관계에 필요한 qualifier·수치·데이터셋·대상·시점이 맞지 않는다.
- 설명의 중요한 문장이 supporting span을 참조하지 않는다.
- 생성기와 auditor의 독립성 정책을 만족하지 않는다.

관계, citation intent, transformation, confidence와 abstention taxonomy는 `docs/03_DOMAIN_TAXONOMY.md` 및 `contracts/taxonomies/`가 정본이다.

## 6. Data and provenance model

지적 저작물인 `work`, 구체적인 출판·원고 버전인 `work_version`, 실제 분석한 bytes인 `source_asset`, 파싱 결과인 `parsed_document`를 분리한다. 동일한 제목의 arXiv 초안과 최종 저널본을 같은 bytes로 취급하지 않는다.

모든 evidence link는 다음을 포함한다.

- atomic citing claim과 문서 좌표
- resolved cited work/version
- citation intent와 evidence relation
- scope observations와 transformations
- source spans 및 exact quote hash/offset
- stage confidence vector
- abstention 또는 limitation
- prompt/model/parser/pipeline/taxonomy version
- source policy와 access decisions
- 생성·검증·감사 producer 기록

DB 제약, RLS, outbox와 canonical columns는 `contracts/db/schema.sql`; API shape는 `contracts/openapi.yaml`; 저장·이벤트 payload는 `contracts/schemas/`와 `contracts/event_catalog.yaml`이 정본이다.

## 7. User experience

기본 reader는 세 영역으로 구성한다.

- **Reference map:** 핵심성, 인용 역할, 현재 reading mode에서의 우선순위, 접근·검증 상태
- **Paper pane:** 현재 논문 원문, 인용 anchor, claim boundary와 좌표
- **Evidence pane:** 현재 주장, 인용 목적, 원문 quote와 위치, 관계·범위·변형, 단계별 confidence, limitation, 원문 열기와 feedback

reading mode는 이해, 구현·재현, 리뷰, 문헌조사, 발표 준비를 지원한다. 우선순위는 논문의 절대 품질 점수가 아니라 사용자의 현재 목적에 대한 상대적 읽기 순서임을 명시한다.

접근성, 반응형 상태, empty/error/blocked state, copy rules는 `docs/08_UX_UI_SPEC.md`가 정본이다.

## 8. Error, uncertainty and recovery

오류는 사용자 입력 오류, 파싱 제한, 식별 충돌, 원문 접근 제한, evidence 부족, 모델·provider 일시 실패, 정책 차단으로 구분한다. 각 결과는 stable reason code, retryability, 사용자 행동, provenance를 제공한다.

시스템은 다음을 단정하지 않는다.

- 메타데이터나 제목 유사성만으로 직접 지지
- 초록에 없는 full-text 실험 결과
- 원문에 존재하지 않는 quote
- 여러 레퍼런스가 묶인 인용에서 모든 대상이 같은 역할이라는 가정
- 다른 버전의 결과를 현재 인용 버전의 결과로 귀속

복구 가능한 상태는 PDF 업로드, 다른 공개 버전 선택, reference identity 확인, 범위 좁히기, 사람 검토 요청 같은 명시적 action을 제공한다.

## 9. Security, privacy and copyright

논문·PDF·TEI·메타데이터·모델 출력은 모두 untrusted input이다. 업로드 크기·페이지·타입·압축 폭탄·악성 링크를 제한하고, 외부 fetch는 DNS/IP/redirect/content-type/size 검사를 거친다. 모델이 문서 속 명령을 실행하거나 임의 URL을 가져오는 것을 금지한다.

workspace data는 PostgreSQL RLS와 object prefix로 격리한다. 로그·trace·metric에는 원문 bytes, quote, prompt, secret과 개인정보를 기본적으로 기록하지 않는다. 공개 공유는 별도의 최소 read model과 취소 가능한 token을 사용한다.

유료벽·인증·접근 통제를 우회하지 않는다. 사용자가 적법하게 제공한 private PDF는 해당 workspace에서만 사용하며, 공개 원문은 license/access provenance를 보존한다. 정본은 `docs/10_SECURITY_PRIVACY_COPYRIGHT.md`, `docs/20_LICENSE_AND_THIRD_PARTY_POLICY.md`, `config/source-policy.example.yaml`이다.

## 10. Testing and release policy

각 구현 task는 실패 테스트 → 최소 구현 → 통과 → regression → commit 순서로 수행한다. 테스트 층은 parser, resolution, retrieval, relation, transformation, explanation, security, API contract, UI/E2E, load와 disaster recovery를 포함한다.

프로덕션 릴리스는 일반 애플리케이션 테스트와 별도로 scientific quality gate를 통과해야 한다. fabricated quote, cross-tenant disclosure, inaccessible source를 full-text로 주장한 사례는 한 건도 허용하지 않는다. 사람 검수 gold set은 최소 300개 인용 사례, 8개 이상 연구 분야, 다중 인용·접근 불가·범위 불일치·변형·비텍스트 근거·적대적 문서를 포함한다.

평가 정책은 `docs/09_EVALUATION_GOLDSET_QA.md`, `eval/`, 요구사항 추적은 `docs/21_REQUIREMENTS_TRACEABILITY_MATRIX.md`가 정본이다.

## 11. Implementation decomposition

설계는 독립 검토 가능한 네 vertical plan으로 실행한다.

1. `plans/2026-08-28-citetrace-foundation-ingestion.md`
2. `plans/2026-08-28-citetrace-reference-resolution-source-acquisition.md`
3. `plans/2026-08-28-citetrace-evidence-engine.md`
4. `plans/2026-08-28-citetrace-reader-quality-production.md`

각 plan은 정확한 파일 경로, public interface, TDD 단계, 실행 명령, 기대 결과, commit과 acceptance gate를 포함한다. 다음 plan은 앞 plan의 gate가 통과된 뒤 시작한다.

## 12. Design self-review result

- **Placeholder scan:** 설계와 네 구현 plan에 TBD/TODO/모호한 “나중에 구현” 지시를 허용하지 않는다.
- **Consistency:** taxonomy, OpenAPI, JSON Schema와 PostgreSQL enum을 자동 비교한다.
- **Scope:** 초기 릴리스는 PDF 중심 claim-to-source traceability에 한정하며, 독립 subsystem은 네 plan으로 분리했다.
- **Ambiguity:** work/version/asset, 접근 수준, support/abstention, confidence/publication status를 별도 개념으로 고정했다.
- **Safety:** paywall bypass, arbitrary model fetch, unsupported quote와 cross-tenant access를 release blocker로 고정했다.

세부 문서와 기계 계약이 충돌할 때는 기계 계약을 자동 검증하고, 의미 변경은 ADR과 schema/version migration을 거쳐 함께 수정한다.
