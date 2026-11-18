// Speaker playback for HA TTS URLs with an analyser for the virtual amplifier level meter.
// createSpeaker({ onLevel }) -> { play, setVolume, stop }; level arrives as dB via onLevel.

import { rmsToDb } from '../domain/audio-level.js';

export function createSpeaker({ onLevel } = {}) {
  let audioContext = null;
  let analyser = null;
  let sourceNode = null;
  let gainNode = null;
  let audioElement = null;
  let rafId = null;
  let volume = 1;
  let pendingResolve = null;

  function setVolume(value) {
    volume = Math.min(1, Math.max(0, Number(value) || 0));
    if (audioElement) audioElement.volume = volume;
  }

  function play(url) {
    return new Promise((resolve, reject) => {
      stopInternal(true);
      pendingResolve = resolve;
      const element = new Audio();
      element.crossOrigin = 'anonymous';
      element.preload = 'auto';
      element.volume = volume;
      audioElement = element;
      element.addEventListener('error', () => onMediaError(url, reject), { once: true });
      element.addEventListener('ended', onEnded, { once: true });
      try {
        attachToGraph(element);
      } catch (err) {
        console.warn('speaker: Web Audio no disponible, se intenta reproducción directa', err);
      }
      element.src = url;
      const playPromise = element.play();
      if (playPromise && typeof playPromise.catch === 'function') {
        playPromise.catch((err) => {
          if (err && err.name === 'NotAllowedError') reject(blockedError());
          else reject({ code: 'E_AUDIO_BLOCKED', message: 'No se pudo reproducir el audio. Toca la página y repite.' });
        });
      }
      startMeter();
    });
  }

  function stop() {
    stopInternal(false);
  }

  function stopInternal(shouldResolvePending) {
    if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
    if (audioElement) {
      audioElement.pause();
      audioElement.removeAttribute('src');
      audioElement.load();
      audioElement = null;
    }
    detachGraph();
    if (shouldResolvePending && pendingResolve) pendingResolve();
    pendingResolve = null;
  }

  function attachToGraph(element) {
    if (!audioContext) audioContext = new AudioContext();
    if (audioContext.state === 'suspended') {
      audioContext.resume().catch((err) => console.warn('speaker: no se pudo reanudar el AudioContext', err));
    }
    sourceNode = audioContext.createMediaElementSource(element);
    gainNode = audioContext.createGain();
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.8;
    sourceNode.connect(analyser);
    analyser.connect(gainNode);
    gainNode.connect(audioContext.destination);
  }

  function detachGraph() {
    if (sourceNode) sourceNode.disconnect();
    if (analyser) analyser.disconnect();
    if (gainNode) gainNode.disconnect();
    sourceNode = null;
    analyser = null;
    gainNode = null;
  }

  function startMeter() {
    if (rafId) cancelAnimationFrame(rafId);
    const tick = () => {
      if (analyser && typeof onLevel === 'function') {
        const samples = new Float32Array(analyser.fftSize);
        analyser.getFloatTimeDomainData(samples);
        onLevel(rmsToDb(samples));
      }
      rafId = requestAnimationFrame(tick);
    };
    rafId = requestAnimationFrame(tick);
  }

  function onEnded() {
    const resolve = pendingResolve;
    stopInternal(false);
    pendingResolve = null;
    if (resolve) resolve();
  }

  function onMediaError(url, reject) {
    // Non-CORS media stays silent through Web Audio; retry once without the graph.
    if (analyser && audioElement) {
      detachGraph();
      audioElement.crossOrigin = null;
      audioElement.src = url;
      audioElement.play().catch(() => reject(blockedError()));
      return;
    }
    reject({ code: 'E_AUDIO_BLOCKED', message: 'No se pudo reproducir el audio. Toca la página y repite.' });
  }

  function blockedError() {
    return { code: 'E_AUDIO_BLOCKED', message: 'El navegador bloqueó el audio. Toca la página y repite.' };
  }

  return { play, setVolume, stop };
}
