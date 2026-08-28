import { describe, it, expect } from 'vitest';
import { transformCoordinates } from '../src/features/reader/pdf/coordinateTransform';

describe('coordinate transform', () => {
  it('transforms based on scale', () => {
    const pt = transformCoordinates({ x: 10, y: 10 }, 2, 0);
    expect(pt.x).toBe(20);
    expect(pt.y).toBe(20);
  });
});
