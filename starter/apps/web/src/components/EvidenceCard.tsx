type EvidenceCardProps = {
  relation: string;
  title: string;
  claim: string;
  quote: string;
  source: string;
  confidence: {
    parse: number;
    resolution: number;
    retrieval: number;
    verification: number;
  };
  limitation?: string;
};

function percentage(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function EvidenceCard({
  relation,
  title,
  claim,
  quote,
  source,
  confidence,
  limitation,
}: EvidenceCardProps) {
  const stages = [
    ["파싱", confidence.parse],
    ["논문 식별", confidence.resolution],
    ["근거 검색", confidence.retrieval],
    ["관계 판정", confidence.verification],
  ] as const;

  return (
    <article className="evidence-card" aria-labelledby="evidence-title">
      <header className="evidence-header">
        <span className="relation-badge">{relation}</span>
        <span className="status-dot">검증됨</span>
      </header>
      <h2 id="evidence-title">{title}</h2>
      <section aria-labelledby="claim-label">
        <p id="claim-label" className="eyebrow">현재 논문의 주장</p>
        <blockquote className="claim">{claim}</blockquote>
      </section>
      <section aria-labelledby="source-label">
        <p id="source-label" className="eyebrow">원문 근거</p>
        <blockquote className="source-quote">“{quote}”</blockquote>
        <p className="source-location">{source}</p>
      </section>
      {limitation ? <p className="limitation">제한: {limitation}</p> : null}
      <section aria-labelledby="confidence-label">
        <p id="confidence-label" className="eyebrow">단계별 신뢰도</p>
        <dl className="confidence-grid">
          {stages.map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{percentage(value)}</dd>
            </div>
          ))}
        </dl>
      </section>
      <div className="card-actions">
        <button type="button">원문 위치 열기</button>
        <button type="button" className="secondary">판정 피드백</button>
      </div>
    </article>
  );
}
