export const openAnalysisStream = (analysisId: string, options?: { lastEventId?: string, onEvent?: (e: any) => void, onError?: (err: any) => void }) => {
  return {
    close: () => {}
  };
};
