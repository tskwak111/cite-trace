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
