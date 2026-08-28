export type ReaderState = {
  status: 'idle' | 'loading' | 'running' | 'completed' | 'completed_with_limits' | 'failed' | 'cancelled' | 'reconnecting';
  selectedReferenceId: string | null;
  activeCitationAnchorId: string | null;
  activeEvidenceLinkId: string | null;
};

export const readerReducer = (state: ReaderState, action: any): ReaderState => {
  return state;
};
