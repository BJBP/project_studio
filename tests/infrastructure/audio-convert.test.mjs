// Tests for audio-convert.js: downsampling ratio, clamping, silence.
import test from 'node:test';
import assert from 'node:assert/strict';
import { downsampleToInt16 } from '../../web/demos/voice/js/infrastructure/audio-convert.js';

test('48 kHz -> 16 kHz: correct output length and averaged blocks', () => {
  const input = new Float32Array(48000).fill(0);
  const out = downsampleToInt16(input, 48000, 16000);
  assert.equal(out.length, 16000);
  assert.ok(out instanceof Int16Array);
});

test('block averaging computes the mean of each ratio-sized block', () => {
  const ramp = new Float32Array([1, -1, 1]);
  const out = downsampleToInt16(ramp, 3, 1);
  assert.equal(out.length, 1);
  assert.equal(out[0], Math.round((1 / 3) * 32767));
});

test('clipping: out-of-range samples are clamped to Int16 bounds', () => {
  const loud = new Float32Array([2, 2, 2, -3, -3, -3]);
  const out = downsampleToInt16(loud, 6, 2);
  assert.deepEqual(Array.from(out), [32767, -32768]);
});

test('silence produces all zeros', () => {
  const silence = new Float32Array(48000);
  const out = downsampleToInt16(silence, 48000, 16000);
  assert.equal(out.length, 16000);
  assert.ok(out.every((sample) => sample === 0));
});

test('default output rate is 16000', () => {
  const input = new Float32Array(480).fill(0);
  assert.equal(downsampleToInt16(input, 48000).length, 160);
});

test('invalid rates are rejected', () => {
  assert.throws(() => downsampleToInt16(new Float32Array(10), 0, 16000), RangeError);
  assert.throws(() => downsampleToInt16(new Float32Array(10), 48000, -1), RangeError);
});
