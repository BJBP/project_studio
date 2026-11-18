import test from "node:test";
import assert from "node:assert/strict";
import { rmsToDb } from "../../web/demos/voice/js/domain/audio-level.js";

test("silence (all zeros) returns -90", () => {
  assert.equal(rmsToDb(new Float32Array(512)), -90);
  assert.equal(rmsToDb([]), -90);
});

test("full-scale signal returns 0 dB", () => {
  const samples = new Float32Array(100).fill(1);
  assert.equal(rmsToDb(samples), 0);
});

test("half-amplitude signal returns about -6 dB", () => {
  const samples = new Float32Array(100).fill(0.5);
  assert.equal(rmsToDb(samples), -6);
});

test("accepts plain arrays and rounds to an integer", () => {
  const db = rmsToDb([0.1, -0.1, 0.1, -0.1]);
  assert.equal(db, Math.round(20 * Math.log10(0.1)));
  assert.equal(Number.isInteger(db), true);
});
