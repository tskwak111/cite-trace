import React from 'react';
import { render, screen } from '@testing-library/react';
import { EvidenceCard } from '../src/features/reader/EvidenceCard';

describe('EvidenceCard', () => {
  const baseProps = {
    relation: '직접 지지',
    accessLevel: '오픈 액세스 전문',
    intents: ['방법 채택'],
    citingContext: { exact: 'Claim text' },
    confidence: { parse: 1, resolution: 1, access: 1, retrieval: 1, relation: 1, explanation: 1 },
    priority: 'high',
  };

  it('renders verified card', () => {
    render(<EvidenceCard {...baseProps} status="verified" />);
    expect(screen.getByTestId('evidence-card-verified')).toBeInTheDocument();
  });

  it('renders limited card', () => {
    render(<EvidenceCard {...baseProps} status="limited" />);
    expect(screen.getByTestId('evidence-card-limited')).toBeInTheDocument();
  });

  it('renders inaccessible card', () => {
    render(<EvidenceCard {...baseProps} status="inaccessible" />);
    expect(screen.getByTestId('evidence-card-inaccessible')).toBeInTheDocument();
  });

  it('renders review_required card', () => {
    render(<EvidenceCard {...baseProps} status="review_required" />);
    expect(screen.getByTestId('evidence-card-review_required')).toBeInTheDocument();
  });
});
