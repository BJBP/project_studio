import test from 'node:test';
import assert from 'node:assert/strict';
import { createMotionWatch } from '../../web/demos/voice/js/application/motion-watch.js';
import { motionRatio } from '../../web/demos/voice/js/domain/motion.js';

test('motionRatio counts changed pixels', () => {
  assert.equal(motionRatio(new Uint8Array([0, 0, 0, 0]), new Uint8Array([0, 200, 0, 200])), 0.5);
  assert.equal(motionRatio(null, new Uint8Array(4)), 0);
});

test('motion turns ON at once and OFF only after the hold time', () => {
  let clock = 0;
  const changes = [];
  const watch = createMotionWatch({ threshold: 0.25, holdMs: 1000, onChange: (on) => changes.push(on), now: () => clock });
  const still = new Uint8Array(4), moved = new Uint8Array([255, 255, 0, 0]);
  watch.frame(still);
  watch.frame(moved);
  clock = 500; watch.frame(moved);
  clock = 900; watch.frame(moved);
  clock = 1500; watch.frame(moved);
  clock = 2600; watch.frame(moved);
  assert.deepEqual(changes, [true, false]);
});
