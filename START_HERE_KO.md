# CiteTrace 개발 패키지 시작 안내

## 이 패키지가 무엇인가

CiteTrace는 논문의 References를 단순히 찾아서 요약하는 서비스가 아니다. **현재 논문의 인용 주장과 인용된 원문의 실제 근거를 문장·표·그림·수식·실험 단위로 연결하고, 지지 정도와 계승·변형 관계를 검증 가능하게 설명하는 에이전트**다.

이 저장소는 아이디어 문서가 아니라 다음을 한 번에 포함한 개발 기준 패키지다.

- 제품 정의와 범위
- 사용자 여정과 기능 요구사항
- 경쟁 전략과 차별화 원칙
- 시스템·데이터·AI 에이전트 아키텍처
- 인용 역할·근거 관계·변형 taxonomy
- OpenAPI·이벤트·JSON Schema·DB 계약
- 프롬프트 팩과 독립 품질 감사 단계
- 골드셋·평가 지표·릴리스 차단 기준
- 보안·개인정보·저작권·합법적 원문 확보 정책
- 운영·비용·관측성·장애 대응 설계
- 구현 순서, 테스트, 파일 경로, 커밋 단위가 있는 실행 계획
- FastAPI API foundation과 Next.js 3-pane reader shell

## 가장 먼저 읽을 파일

1. `docs/00_MASTER_BLUEPRINT.md` — 전체 제품과 기술 설계의 단일 기준
2. `docs/01_PRODUCT_REQUIREMENTS_PRD.md` — 실제 사용자가 무엇을 할 수 있어야 하는지
3. `docs/05_AGENT_AI_PIPELINE.md` — 에이전트가 근거를 찾고 검증하는 전체 과정
4. `docs/09_EVALUATION_GOLDSET_QA.md` — “잘 된다”를 어떻게 증명할지
5. `docs/12_ROADMAP_BACKLOG.md` — 어떤 순서로 만들지
6. `docs/superpowers/plans/README.md` — 개발자가 실행할 네 개 구현 계획

## 핵심 제품 원칙

- **근거를 먼저 저장하고 설명은 나중에 생성한다.**
- **원문과 정확히 일치하지 않는 quote는 표시하지 않는다.**
- **전문을 확보하지 못하면 초록·메타데이터 수준을 숨기지 않는다.**
- **판단할 근거가 부족하면 실패한 척하지 않고 보류 결과를 낸다.**
- **유료 장벽이나 접근 통제를 우회하지 않는다.**
- **사용자 문서의 내용은 도구 명령이 아니라 신뢰하지 않는 데이터다.**
- **파싱·논문 식별·원문 접근·근거 검색·관계 판정·설명 신뢰도를 분리한다.**
- **프롬프트나 모델 변경은 골드셋 회귀 평가 없이 배포하지 않는다.**

## 구현 계획의 권장 순서

### 1단계 — Foundation & Ingestion

`docs/superpowers/plans/2026-08-28-citetrace-foundation-ingestion.md`

API, 워크스페이스 격리, 업로드 검증, PDF 격리 처리, GROBID 파싱, 정규화 좌표, 인용 anchor와 레퍼런스 추출까지 만든다.

### 2단계 — Reference Resolution & Source Acquisition

`docs/superpowers/plans/2026-08-28-citetrace-reference-resolution-source-acquisition.md`

Crossref·OpenAlex·Semantic Scholar 등의 메타데이터 후보를 모으고, 잘못된 DOI/버전 매칭을 차단하며, 사용자 업로드·오픈 저장소·공개 원문·초록을 합법적 정책에 따라 확보한다.

### 3단계 — Evidence Engine

`docs/superpowers/plans/2026-08-28-citetrace-evidence-engine.md`

현재 논문의 claim을 분해하고, cited source에서 후보 근거를 하이브리드 검색·재정렬하며, 관계와 변형을 구조화해 판정하고, 모든 quote를 원문 offset/hash로 검증한다.

### 4단계 — Reader, Quality & Production

`docs/superpowers/plans/2026-08-28-citetrace-reader-quality-production.md`

3-pane reader, 신뢰도·보류·피드백 UI, lineage graph, 평가 자동화, 관측성, 비용 제한, 운영 보안, 배포·롤백 체계를 완성한다.

## 현재 실행 가능한 foundation

`starter/`는 완성된 제품이 아니라 계약과 개발 방식이 실제로 작동하는지 확인하는 foundation이다.

포함된 것:

- 분석 생성·조회·취소·목록·SSE API
- 요청 멱등성
- 닫힌 상태 전이
- 정확한 quote/offset/hash 검증
- Problem Details 오류 형식
- API 단위 테스트
- 3-pane 논문·레퍼런스·근거 UI shell
- PostgreSQL/pgvector, Redis, GROBID Compose 구성
- CI 예시

아직 구현 계획에 남아 있는 것:

- 인증과 실제 DB repository
- 보안 업로드·오브젝트 스토리지
- GROBID 호출과 TEI 정규화
- 외부 학술 API adapter
- 합법적 원문 확보
- 하이브리드 검색·reranker
- 모델 gateway와 verifier/auditor
- 실제 PDF 좌표 렌더링
- 300–500개 인간 검수 골드셋
- 프로덕션 클라우드·관측성·운영 자동화

## 기본 검증 명령

v1.7 (14 슬라이스 + 5 ADR + 8 태그)에서는 패키지 루트의 `make check`
타겟이 모든 오프라인 검증을 한 번에 실행합니다:

```bash
make check
```

`make check`는 다음을 차례로 실행합니다:

- 7/8 contract validators (`validate_package.py`) — OpenAPI 검증 1건은
  알려진 v1.8 blocker
- `validate_eval_assets.py`
- 204 API tests (`pytest`)
- 20 ops tests (`pytest`)
- web typecheck / vitest / production build

추가로 라이브 통합 (Docker 필요) 검증은 `README.md` §4를 참고하세요.

상세 명령을 따로 실행하려면:

```bash
# 1. contracts
uv run --no-project --with pyyaml --with jsonschema \
  --with openapi-spec-validator python scripts/validate_package.py
uv run --no-project --with pyyaml python scripts/validate_eval_assets.py

# 2. API
cd starter/services/api && pytest -q tests

# 3. ops
cd starter/ops && ../services/api/.venv/bin/pytest tests -q

# 4. web
cd starter/apps/web && pnpm typecheck && pnpm test && pnpm build
```

릴리스 절차는 README.md §4 "Cut a release"를 참고하세요.

## 반드시 구분해야 하는 것

- `docs/00_MASTER_BLUEPRINT.md`: 무엇을 왜 만들지에 대한 최상위 기준
- `contracts/`: 서비스끼리 반드시 지켜야 하는 기계 계약
- `prompts/`: 모델에게 맡기는 제한된 판단 작업
- `eval/`: 모델과 시스템이 실제로 정확한지 판정하는 기준
- `docs/superpowers/plans/`: 구현자가 어떤 파일을 어떤 테스트와 함께 만들지
- `starter/`: 위 기준을 실행 코드로 연결하기 위한 출발점

제품 판단이 애매할 때는 문서의 문장보다 **근거 선행·정확 quote·합법적 접근·명시적 보류·사용자 검증 가능성**을 우선한다.
