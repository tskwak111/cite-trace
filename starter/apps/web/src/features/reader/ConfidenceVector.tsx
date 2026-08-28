import React from 'react';

export const ConfidenceVector: React.FC<{ scores: Record<string, number> }> = ({ scores }) => {
  return (
    <div className="confidence-vector">
      {Object.entries(scores).map(([stage, score]) => (
        <div key={stage}>
          {stage}: {score}
        </div>
      ))}
    </div>
  );
};
