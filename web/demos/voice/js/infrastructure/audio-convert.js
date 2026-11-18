// Pure audio conversion helpers for the voice demo. No browser or DOM dependencies.
// downsampleToInt16(float32Samples, inputRate, outputRate) -> Int16Array via per-block averaging.

export function downsampleToInt16(float32Samples, inputRate, outputRate = 16000) {
  if (!Number.isFinite(inputRate) || !Number.isFinite(outputRate) || inputRate <= 0 || outputRate <= 0) {
    throw new RangeError('Las tasas de muestreo deben ser mayores que 0.');
  }
  if (!float32Samples || typeof float32Samples.length !== 'number') {
    throw new TypeError('float32Samples debe ser un array o TypedArray.');
  }
  const ratio = inputRate / outputRate;
  const outLength = Math.floor(float32Samples.length / ratio);
  const out = new Int16Array(outLength);
  for (let i = 0; i < outLength; i += 1) {
    const start = Math.floor(i * ratio);
    const end = Math.floor((i + 1) * ratio);
    const span = Math.max(1, end - start);
    let sum = 0;
    for (let j = start; j < end; j += 1) sum += float32Samples[j];
    out[i] = clampToInt16(Math.round((sum / span) * 32767));
  }
  return out;
}

function clampToInt16(value) {
  if (value > 32767) return 32767;
  if (value < -32768) return -32768;
  return value;
}
