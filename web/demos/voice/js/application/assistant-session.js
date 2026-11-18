// Assistant session: links mic, assist and speaker into one talk flow.
// createAssistantSession({ assist, mic, speaker, handlers })
//   -> { startTalking, stopTalking, startHandsFree, stopHandsFree, isHandsFree, sendText, forwardChunk, setPipeline }.
// Hands-free: the mic stays open and each run waits for the wake word; after the answer a new run waits again.
// handlers: { onStatus(key), onHeard(text), onAnswer(text), onLevel(db), onError({ code, message }) }.

export function createAssistantSession({ assist, mic, speaker, handlers = {} } = {}) {
  if (!assist || !mic || !speaker) {
    throw new TypeError('createAssistantSession: assist, mic y speaker son obligatorios');
  }
  let audio = null;
  let status = 'idle';
  let speaking = false;
  let pipelineId = null; // which AI answers; null = HA's preferred assistant
  let handsFree = false;
  const restStatus = () => (handsFree ? 'waiting' : 'idle');

  function setStatus(next) {
    status = next;
    handlers.onStatus?.(next);
  }

  function reportError(error) {
    const normalized = normalizeError(error);
    setStatus('idle');
    handlers.onError?.(normalized);
  }

  function pipelineHandlers() {
    return {
      onHeard: (text) => {
        setStatus('thinking');
        handlers.onHeard?.(text);
      },
      onAnswer: (text) => handlers.onAnswer?.(text),
      onAudio: (url) => {
        speaking = true;
        setStatus('speaking');
        speaker.play(url).then(finishSpeaking, reportError);
      },
      onDone: () => {
        if (!speaking) setStatus(restStatus());
      },
      onError: reportError,
    };
  }

  function finishSpeaking() {
    speaking = false;
    setStatus(restStatus());
  }

  async function startTalking() {
    if (audio || handsFree) return; // hands-free already listens
    setStatus('listening');
    try {
      audio = assist.startAudio(pipelineHandlers(), pipelineId);
    } catch (error) {
      reportError(error);
      return;
    }
    try {
      await mic.start();
    } catch (error) {
      try { audio?.end?.(); } catch (endError) { console.warn('assistant-session: no se pudo cerrar el pipeline de audio', endError); }
      audio = null;
      reportError(error);
    }
  }

  function stopTalking() {
    if (handsFree) return;
    mic.stop();
    if (!audio) return;
    audio.end();
    audio = null;
    if (status === 'listening') setStatus('thinking');
  }

  function forwardChunk(int16) {
    audio?.sendChunk(int16);
  }

  function sendText(text) {
    const clean = String(text ?? '').trim();
    if (!clean) {
      handlers.onError?.({ code: 'E_EMPTY_INPUT', message: 'Escribe una orden primero.' });
      return;
    }
    setStatus('thinking');
    try {
      assist.runText(clean, pipelineHandlers(), pipelineId);
    } catch (error) {
      reportError(error);
    }
  }

  // HA ends each run itself (silence after the order); a timeout while waiting for the word just restarts it.
  function openWakeRun() {
    const base = pipelineHandlers();
    try {
      audio = assist.startAudio({
        ...base,
        onWake: () => setStatus('listening'),
        onDone: () => { audio = null; base.onDone(); if (handsFree) openWakeRun(); },
        onError: (error) => {
          if (WAKE_TIMEOUTS.has(error?.code)) return; // run-end follows and opens the next run
          stopHandsFree();
          reportError(error);
        },
      }, pipelineId, { wakeWord: true });
      if (!speaking) setStatus('waiting');
    } catch (error) {
      stopHandsFree();
      reportError(error);
    }
  }

  async function startHandsFree() {
    if (handsFree) return;
    handsFree = true;
    openWakeRun();
    try {
      await mic.start();
    } catch (error) {
      stopHandsFree();
      reportError(error);
    }
  }

  function stopHandsFree() {
    if (!handsFree) return;
    handsFree = false;
    mic.stop();
    const open = audio;
    audio = null;
    try { open?.end(); } catch (error) { console.warn('assistant-session: no se pudo cerrar la escucha', error); }
    setStatus('idle');
  }

  const setPipeline = (id) => { pipelineId = id || null; };

  const isHandsFree = () => handsFree;

  return { startTalking, stopTalking, startHandsFree, stopHandsFree, isHandsFree, sendText, forwardChunk, setPipeline };
}

const WAKE_TIMEOUTS = new Set(['wake-word-timeout', 'timeout']);

function normalizeError(error) {
  if (error && typeof error === 'object' && error.code) return error;
  return { code: 'E_ASSIST', message: error?.message || 'Falló el asistente. ¿Está arrancado el stack?' };
}
