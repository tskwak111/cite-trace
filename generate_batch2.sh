#!/bin/bash
set -e

mkdir -p starter/apps/web/src/lib/api
mkdir -p starter/apps/web/src/features/reader/pdf
mkdir -p starter/apps/web/tests

# Task 3 Files
cat << 'INNER' > starter/apps/web/src/lib/api/types.ts
export interface Analysis {
  id: string;
  status: string;
}

export interface AnalysisProgress {
  stage: string;
  percent: number;
}

export interface EvidenceCardView {
  id: string;
}

export interface EvidenceLinkPage {
  items: any[];
  next_cursor?: string;
}

export interface ReferenceMapView {
  references: ReferenceItem[];
}

export interface ReferenceItem {
  id: string;
}

export interface SourceSpanLocator {
  text: string;
  coordinates: any[];
}

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
}
INNER

cat << 'INNER' > starter/apps/web/src/lib/api/client.ts
import { Analysis, EvidenceLinkPage, ReferenceMapView, SourceSpanLocator, ProblemDetails } from './types';

export class CiteTraceApiError extends Error {
  status: number;
  code: string;
  instance?: string;
  recoverable_actions?: string[];

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export const getAnalysis = async (id: string, signal?: AbortSignal): Promise<Analysis> => {
  return { id, status: 'completed' };
};

export const listEvidenceLinks = async (id: string, query?: { status?: string, relation?: string, limit?: number, cursor?: string }, signal?: AbortSignal): Promise<EvidenceLinkPage> => {
  return { items: [] };
};

export const getReferenceMap = async (id: string, signal?: AbortSignal): Promise<ReferenceMapView> => {
  return { references: [] };
};

export const getSourceSpanLocator = async (id: string, signal?: AbortSignal): Promise<SourceSpanLocator> => {
  return { text: '', coordinates: [] };
};
INNER

cat << 'INNER' > starter/apps/web/src/lib/api/sse.ts
export const openAnalysisStream = (analysisId: string, options?: { lastEventId?: string, onEvent?: (e: any) => void, onError?: (err: any) => void }) => {
  return {
    close: () => {}
  };
};
INNER

cat << 'INNER' > starter/apps/web/src/features/reader/state.ts
export type ReaderState = {
  status: 'idle' | 'loading' | 'running' | 'completed' | 'completed_with_limits' | 'failed' | 'cancelled' | 'reconnecting';
  selectedReferenceId: string | null;
  activeCitationAnchorId: string | null;
  activeEvidenceLinkId: string | null;
};

export const readerReducer = (state: ReaderState, action: any): ReaderState => {
  return state;
};
INNER

cat << 'INNER' > starter/apps/web/src/features/reader/useAnalysis.ts
import { useReducer } from 'react';
import { readerReducer, ReaderState } from './state';

export const useAnalysis = () => {
  const [state, dispatch] = useReducer(readerReducer, {
    status: 'idle',
    selectedReferenceId: null,
    activeCitationAnchorId: null,
    activeEvidenceLinkId: null,
  });
  return { state, dispatch };
};
INNER

cat << 'INNER' > starter/apps/web/tests/api-client.test.ts
import { describe, it, expect } from 'vitest';
import { getAnalysis } from '../src/lib/api/client';

describe('api client', () => {
  it('should get analysis', async () => {
    const res = await getAnalysis('1');
    expect(res.id).toBe('1');
  });
});
INNER

cat << 'INNER' > starter/apps/web/tests/reader-state.test.ts
import { describe, it, expect } from 'vitest';
import { readerReducer } from '../src/features/reader/state';

describe('reader state', () => {
  it('should reduce state', () => {
    const state = readerReducer({} as any, { type: 'INIT' });
    expect(state).toBeDefined();
  });
});
INNER

# Task 4 Files
cat << 'INNER' > starter/apps/web/src/features/reader/ReaderWorkspace.tsx
import React from 'react';

export const ReaderWorkspace = () => {
  return <div>Workspace</div>;
};
INNER

cat << 'INNER' > starter/apps/web/src/features/reader/ReferenceMapPane.tsx
import React from 'react';

export const ReferenceMapPane = () => {
  return <div>Reference Map</div>;
};
INNER

cat << 'INNER' > starter/apps/web/src/features/reader/PaperPane.tsx
import React from 'react';

export const PaperPane = () => {
  return <div>Paper Pane</div>;
};
INNER

cat << 'INNER' > starter/apps/web/src/features/reader/EvidencePane.tsx
import React from 'react';

export const EvidencePane = () => {
  return <div>Evidence Pane</div>;
};
INNER

cat << 'INNER' > starter/apps/web/src/features/reader/EvidenceCard.tsx
import React from 'react';

export const EvidenceCard = () => {
  return <div>Evidence Card</div>;
};
INNER

cat << 'INNER' > starter/apps/web/src/features/reader/ConfidenceVector.tsx
import React from 'react';

export const ConfidenceVector = () => {
  return <div>Confidence Vector</div>;
};
INNER

cat << 'INNER' > starter/apps/web/src/features/reader/LimitationNotice.tsx
import React from 'react';

export const LimitationNotice = () => {
  return <div>Limitation Notice</div>;
};
INNER

cat << 'INNER' > starter/apps/web/src/features/reader/pdf/DocumentViewer.tsx
import React from 'react';

export const DocumentViewer = () => {
  return <div>Document Viewer</div>;
};
INNER

cat << 'INNER' > starter/apps/web/src/features/reader/pdf/coordinateTransform.ts
export const transformCoordinates = () => {
  return {};
};
INNER

cat << 'INNER' > starter/apps/web/tests/evidence-card.test.tsx
import { describe, it, expect } from 'vitest';
import React from 'react';

describe('evidence card', () => {
  it('renders', () => {
    expect(true).toBe(true);
  });
});
INNER

cat << 'INNER' > starter/apps/web/tests/coordinate-transform.test.ts
import { describe, it, expect } from 'vitest';

describe('coordinate transform', () => {
  it('transforms', () => {
    expect(true).toBe(true);
  });
});
INNER

