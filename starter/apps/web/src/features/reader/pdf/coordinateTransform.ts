export type Point = { x: number; y: number };
export type Rect = { x: number; y: number; width: number; height: number };

export const transformCoordinates = (point: Point, scale: number, rotation: number): Point => {
  // Mock logic
  return {
    x: point.x * scale,
    y: point.y * scale,
  };
};
