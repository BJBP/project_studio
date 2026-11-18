// Assistant session: links mic, assist and speaker into one talk flow.
// createAssistantSession({ assist, mic, speaker, handlers }) -> { startTalking, stopTalking, sendText, forwardChunk, setPipeline }.
// handlers: { onStatus(key), onHeard(text), onAnswer(text), onLevel(db), onError({ code, message }) }.

export function createAssistantSession({ assist, mic, speaker, handlers = {} } = {}) {
  if (!assist || !mic || !speaker) {
    throw new TypeError('createAssistantSession: assist, mic y speaker son obligatorios');
  }
  let audio = null;
  let status = 'idle';
  let speaking = false;
  let pipelineId = null; // which AI answers; null = HA's preferred assistant

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
        if (!speaking) setStatus('idle');
      },
      onError: reportError,
    };
  }

  function finishSpeaking() {
    speaking = false;
    setStatus('idle');
  }

  async function startTalking() {
    if (audio) return;
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

  const setPipeline = (id) => { pipelineId = id || null; };

  return { startTalking, stopTalking, sendText, forwardChunk, setPipeline };
}

function normalizeError(error) {
  if (error && typeof error === 'object' && error.code) return error;
  return { code: 'E_ASSIST', message: error?.message || 'Falló el asistente. ¿Está arrancado el stack?' };
}
