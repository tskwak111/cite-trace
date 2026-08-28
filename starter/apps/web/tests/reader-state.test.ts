import { describe, it, expect } from 'vitest';
import { readerReducer } from '../src/features/reader/state';

describe('reader state', () => {
  it('should reduce state', () => {
    const state = readerReducer({} as any, { type: 'INIT' });
    expect(state).toBeDefined();
  });
});
