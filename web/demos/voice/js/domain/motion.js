// Motion from two small grayscale frames. motionRatio(prev, next, pixelDelta) -> share of pixels that changed.
// SENSITIVITY maps the user's choice to the share that counts as movement.
export const SENSITIVITY = { low: 0.08, medium: 0.03, high: 0.01 };
const DEFAULT_PIXEL_DELTA = 28; // brightness change (0–255) that counts as a changed pixel

export function motionRatio(prev, next, pixelDelta = DEFAULT_PIXEL_DELTA) {
  if (!prev || !next || prev.length !== next.length || !next.length) return 0;
  let changed = 0;
  for (let i = 0; i < next.length; i += 1) if (Math.abs(next[i] - prev[i]) > pixelDelta) changed += 1;
  return changed / next.length;
}
