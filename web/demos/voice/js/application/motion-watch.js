// Turns camera frames into a motion sensor: ON when enough pixels change, OFF after holdMs without movement.
// createMotionWatch({ threshold, holdMs, onChange(on), now? }) -> { frame(gray), reset() }.
import { motionRatio } from '../domain/motion.js';

export function createMotionWatch({ threshold, holdMs, onChange, now = () => Date.now() }) {
  let previous = null, active = false, lastMotion = 0;

  function frame(gray) {
    const moved = motionRatio(previous, gray) >= threshold;
    previous = gray;
    if (moved) lastMotion = now();
    const next = moved || (active && now() - lastMotion < holdMs);
    if (next !== active) { active = next; onChange(active); }
  }

  function reset() {
    previous = null;
    if (active) { active = false; onChange(false); }
  }

  return { frame, reset };
}
