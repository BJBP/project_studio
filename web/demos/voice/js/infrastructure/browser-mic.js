// Browser microphone capture: getUserMedia -> AudioContext -> AudioWorklet ('studio-mic').
// createBrowserMic({ onChunk, onLevel }) -> { start, stop }; chunks are Int16Array @16 kHz.

import { downsampleToInt16 } from './audio-convert.js';
import { rmsToDb } from '../domain/audio-level.js';

const TARGET_RATE = 16000;

export function createBrowserMic({ onChunk, onLevel } = {}) {
  let audioContext = null;
  let stream = null;
  let source = null;
  let workletNode = null;
  let muteGain = null;

  async function start() {
    if (audioContext) return;
    stream = await requestStream();
    audioContext = new AudioContext();
    try {
      await audioContext.audioWorklet.addModule(new URL('./mic-worklet.js', import.meta.url));
    } catch (err) {
      await releaseCapture();
      throw { code: 'E_MIC_UNAVAILABLE', message: 'No se pudo cargar el procesador de audio. Recarga la página.' };
    }
    source = audioContext.createMediaStreamSource(stream);
    workletNode = new AudioWorkletNode(audioContext, 'studio-mic');
    workletNode.port.onmessage = (event) => handleBlock(event.data);
    // A zero-gain node keeps the graph pulling samples without echoing the mic to the speakers.
    muteGain = audioContext.createGain();
    muteGain.gain.value = 0;
    source.connect(workletNode);
    workletNode.connect(muteGain);
    muteGain.connect(audioContext.destination);
  }

  function stop() {
    if (workletNode) {
      workletNode.port.onmessage = null;
      workletNode.disconnect();
    }
    if (source) source.disconnect();
    if (muteGain) muteGain.disconnect();
    if (stream) for (const track of stream.getTracks()) track.stop();
    if (audioContext) {
      audioContext.close().catch((err) => console.warn('browser-mic: no se pudo cerrar el AudioContext', err));
    }
    audioContext = null;
    stream = null;
    source = null;
    workletNode = null;
    muteGain = null;
  }

  function handleBlock(float32Block) {
    if (!float32Block || !float32Block.length) return;
    if (typeof onChunk === 'function') {
      onChunk(downsampleToInt16(float32Block, audioContext.sampleRate, TARGET_RATE));
    }
    if (typeof onLevel === 'function') {
      onLevel(rmsToDb(float32Block));
    }
  }

  async function releaseCapture() {
    if (stream) for (const track of stream.getTracks()) track.stop();
    if (audioContext) {
      await audioContext.close().catch((err) => console.warn('browser-mic: no se pudo cerrar el AudioContext', err));
    }
    stream = null;
    audioContext = null;
  }

  async function requestStream() {
    try {
      return await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      });
    } catch (err) {
      if (err && (err.name === 'NotAllowedError' || err.name === 'SecurityError')) {
        throw { code: 'E_MIC_DENIED', message: 'Permite el micrófono en el candado de la barra de direcciones.' };
      }
      throw { code: 'E_MIC_UNAVAILABLE', message: 'No hay micrófono disponible o está en uso por otra aplicación.' };
    }
  }

  return { start, stop };
}
