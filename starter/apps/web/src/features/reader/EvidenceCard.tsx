import React from 'react';
import { ConfidenceVector } from './ConfidenceVector';
import { LimitationNotice } from './LimitationNotice';

export type EvidenceCardProps = {
  relation: string;
  accessLevel: string;
  intents: string[];
  citingContext: { exact: string, before?: string, after?: string };
  sourceQuote?: { exact: string, section?: string, page?: string };
  transformation?: { type: string, explanation: string };
  confidence: { parse: number, resolution: number, access: number, retrieval: number, relation: number, explanation: number };
  priority: string;
  recommendedSections?: string[];
  status: 'verified' | 'limited' | 'inaccessible' | 'review_required';
};

export const EvidenceCard: React.FC<EvidenceCardProps> = ({
  relation, accessLevel, intents, citingContext, sourceQuote, transformation, confidence, priority, recommendedSections, status
}) => {
  return (
    <div className={`evidence-card status-${status}`} data-testid={`evidence-card-${status}`}>
      <div className="header">
        <span className="relation-badge">{relation}</span>
        <span className="access-disclosure">{accessLevel}</span>
        <span className="priority-badge">{priority}</span>
      </div>
      <div className="intents">
        {intents.map(intent => <span key={intent} className="intent-badge">{intent}</span>)}
      </div>
      <div className="citing-context">
        <blockquote>{citingContext.before} <mark>{citingContext.exact}</mark> {citingContext.after}</blockquote>
      </div>
      <div className="source-quote">
        {sourceQuote ? (
          <blockquote>
            {sourceQuote.exact}
            <footer>{sourceQuote.section && `Section: ${sourceQuote.section}`} {sourceQuote.page && `Page: ${sourceQuote.page}`}</footer>
          </blockquote>
        ) : (
          <LimitationNotice message="Exact source quote unavailable" />
        )}
      </div>
      {transformation && (
        <div className="transformation">
          <span className="transformation-badge">{transformation.type}</span>
          <p>{transformation.explanation}</p>
        </div>
      )}
      <ConfidenceVector scores={confidence} />
      <div className="actions">
        <button>원문 위치 열기</button>
        <button>Feedback</button>
      </div>
    </div>
  );
};
