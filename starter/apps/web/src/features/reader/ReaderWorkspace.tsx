import React from 'react';
import { ReferenceMapPane } from './ReferenceMapPane';
import { PaperPane } from './PaperPane';
import { EvidencePane } from './EvidencePane';

export const ReaderWorkspace = () => {
  return (
    <div className="reader-workspace">
      <ReferenceMapPane />
      <PaperPane />
      <EvidencePane />
    </div>
  );
};
