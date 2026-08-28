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
