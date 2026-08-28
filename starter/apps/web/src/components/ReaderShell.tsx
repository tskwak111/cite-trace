import { EvidenceCard } from "./EvidenceCard";

const references = [
  { id: "[12]", title: "Foundation method", role: "방법 채택", priority: "필수" },
  { id: "[15]", title: "Benchmark dataset", role: "데이터셋 사용", priority: "높음" },
  { id: "[18]", title: "Contrasting result", role: "결과 대조", priority: "검토" },
];

export function ReaderShell() {
  return (
    <main className="reader-shell">
      <header className="topbar">
        <div>
          <p className="product-mark">CiteTrace</p>
          <p className="document-title">Evidence-first paper reading workspace</p>
        </div>
        <div className="topbar-actions">
          <span className="mode-pill">이해 모드 · 초급</span>
          <button type="button">분석 시작</button>
        </div>
      </header>

      <aside className="reference-rail" aria-label="핵심 레퍼런스">
        <div className="rail-heading">
          <p className="eyebrow">레퍼런스 지도</p>
          <strong>54개 중 핵심 7개</strong>
        </div>
        <nav>
          {references.map((reference, index) => (
            <button className={index === 0 ? "reference active" : "reference"} key={reference.id}>
              <span className="reference-id">{reference.id}</span>
              <span>
                <strong>{reference.title}</strong>
                <small>{reference.role} · {reference.priority}</small>
              </span>
            </button>
          ))}
        </nav>
        <div className="rail-summary">
          <p><span>직접 지지</span><strong>11</strong></p>
          <p><span>부분·간접</span><strong>8</strong></p>
          <p><span>검토 필요</span><strong>4</strong></p>
          <p><span>접근 불가</span><strong>3</strong></p>
        </div>
      </aside>

      <section className="paper-pane" aria-label="논문 본문">
        <div className="paper-toolbar">
          <span>5 / 14 페이지</span>
          <span>인용 하이라이트 켜짐</span>
        </div>
        <article className="paper-page">
          <p className="paper-section">3. Method</p>
          <h1>Cross-document evidence alignment</h1>
          <p>
            We employ a multi-stage retrieval process that preserves claim qualifiers and exact
            source coordinates. The core encoder follows the architecture proposed in
            <mark>[12]</mark>, while the query planner is adapted to citation-specific scope.
          </p>
          <p>
            Unlike generic semantic search, candidate spans are reranked with dataset, metric,
            population, and negation constraints. This prevents a topically similar paragraph
            from being presented as direct support.
          </p>
          <div className="method-box">
            <strong>Method change detected</strong>
            <p>Base architecture retained · query construction extended · domain transferred</p>
          </div>
          <p>
            Every accepted quote is validated against immutable source bytes before it can be
            displayed. Generated explanations are published only after statement-level grounding
            and access-policy checks.
          </p>
        </article>
      </section>

      <aside className="evidence-pane" aria-label="인용 근거 분석">
        <div className="pane-heading">
          <p className="eyebrow">선택한 인용 [12]</p>
          <h1>왜 인용했고, 무엇을 가져왔는가</h1>
        </div>
        <EvidenceCard
          relation="직접 지지"
          title="핵심 구조는 원 논문에서 채택했고 검색 단계는 확장했습니다."
          claim="The core encoder follows the architecture proposed in [12]."
          quote="The encoder maps each input into a contextual representation before pairwise comparison."
          source="Section 3.1 · p.4 · exact span verified"
          confidence={{ parse: 0.99, resolution: 0.96, retrieval: 0.91, verification: 0.88 }}
        />
        <section className="difference-panel">
          <p className="eyebrow">계승·변형</p>
          <ul>
            <li><strong>그대로 채택:</strong> contextual encoder structure</li>
            <li><strong>확장:</strong> citation-aware query planning</li>
            <li><strong>사용하지 않음:</strong> source paper&apos;s original sampling schedule</li>
          </ul>
        </section>
      </aside>
    </main>
  );
}
