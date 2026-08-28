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
