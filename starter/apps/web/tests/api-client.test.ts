import { describe, it, expect } from 'vitest';
import { getAnalysis } from '../src/lib/api/client';

describe('api client', () => {
  it('should get analysis', async () => {
    const res = await getAnalysis('1');
    expect(res.id).toBe('1');
  });
});
