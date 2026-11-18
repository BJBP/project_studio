// Converts a block of audio samples into a decibel level. Receives samples
// (Float32Array or array, values in -1..1), returns dB rounded to an integer,
// clamped to a minimum of -90 (silence).
export function rmsToDb(samples) {
  if (!samples || samples.length === 0) return -90;
  let sum = 0;
  for (const sample of samples) {
    const s = Number(sample) || 0;
    sum += s * s;
  }
  const rms = Math.sqrt(sum / samples.length);
  if (rms === 0) return -90;
  const db = Math.round(20 * Math.log10(rms));
  return Math.max(-90, db);
}
