// Home Assistant Assist pipeline client over the HA WebSocket API (/api/websocket).
// createAssist({ haUrl, token, WebSocketImpl? }) -> { connect, runText, startAudio, request, close }.
// request(command) sends any other HA WebSocket command and resolves with its result.
// Errors surface as { code: 'E_...', message } objects; handlers receive plain data.

export function createAssist({ haUrl, token, WebSocketImpl } = {}) {
  const WS = WebSocketImpl || globalThis.WebSocket;
  const base = String(haUrl || '').replace(/\/+$/, '');
  const wsUrl = `${base.replace(/^http/i, 'ws')}/api/websocket`;
  const pipelines = new Map();
  const requests = new Map();
  let ws = null, nextId = 1, authenticated = false, connectPromise = null, settleConnect = null;

  function connect() {
    if (authenticated) return Promise.resolve();
    if (connectPromise) return connectPromise;
    if (!WS) return Promise.reject({ code: 'E_HA_DOWN', message: 'Este navegador no soporta WebSocket. Usa Chrome o Edge.' });
    connectPromise = new Promise((resolve, reject) => {
      const timer = setTimeout(() => handleDrop(), 5000);
      settleConnect = (error) => {
        clearTimeout(timer);
        connectPromise = null;
        settleConnect = null;
        return error ? reject(error) : resolve();
      };
      try {
        ws = new WS(wsUrl);
      } catch (err) {
        clearTimeout(timer);
        connectPromise = null;
        settleConnect = null;
        reject(downError());
        return;
      }
      ws.onmessage = (event) => handleMessage(event);
      ws.onerror = () => handleDrop();
      ws.onclose = () => handleDrop();
    });
    return connectPromise;
  }

  function runText(text, handlers = {}) {
    return registerPipeline({ start_stage: 'intent', end_stage: 'tts', input: { text } }, handlers);
  }

  function startAudio(handlers = {}) {
    const state = { binaryHandlerId: null, pending: [], ended: false };
    registerPipeline({ start_stage: 'stt', end_stage: 'tts', input: { sample_rate: 16000 } }, handlers, state);
    return {
      sendChunk(int16) {
        if (state.ended || !int16 || !int16.byteLength) return;
        if (state.binaryHandlerId == null) state.pending.push({ kind: 'chunk', int16 });
        else sendBinaryFrame(state.binaryHandlerId, int16);
      },
      end() {
        if (state.ended) return;
        state.ended = true;
        if (state.binaryHandlerId == null) state.pending.push({ kind: 'end' });
        else sendBinaryFrame(state.binaryHandlerId, null);
      },
    };
  }

  function request(command) {
    if (!ws) return Promise.reject({ code: 'E_HA_DOWN', message: 'No hay conexión con Home Assistant. Llama a connect() primero.' });
    const id = nextId;
    nextId += 1;
    ws.send(JSON.stringify({ id, ...command }));
    return new Promise((resolve, reject) => requests.set(id, { resolve, reject }));
  }

  const close = () => { pipelines.clear(); teardown(); };

  function registerPipeline(command, handlers, audioState = null) {
    if (!ws) throw { code: 'E_HA_DOWN', message: 'No hay conexión con Home Assistant. Llama a connect() primero.' };
    const id = nextId;
    nextId += 1;
    pipelines.set(id, { handlers, audioState });
    ws.send(JSON.stringify({ id, type: 'assist_pipeline/run', ...command }));
    return id;
  }

  function handleMessage(rawEvent) {
    const data = rawEvent && rawEvent.data !== undefined ? rawEvent.data : rawEvent;
    let msg = null;
    try {
      msg = JSON.parse(typeof data === 'string' ? data : String(data));
    } catch (err) {
      console.warn('ha-assist: mensaje no-JSON ignorado', err);
      return;
    }
    if (msg.type === 'auth_required') return ws.send(JSON.stringify({ type: 'auth', access_token: token }));
    if (msg.type === 'auth_ok') { authenticated = true; settleConnect?.(null); return; }
    if (msg.type === 'auth_invalid') return failAuth();
    if (msg.type === 'event' && msg.id != null) return dispatchEvent(msg.id, msg.event || {});
    if (msg.type === 'result' && requests.has(msg.id)) return settleRequest(msg);
    if (msg.type === 'result' && msg.id != null && !msg.success) {
      pipelines.get(msg.id)?.handlers.onError?.({ code: 'E_ASSIST', message: msg.error?.message || 'Home Assistant rechazó la orden.' });
      pipelines.delete(msg.id);
    }
  }

  function settleRequest(msg) {
    const { resolve, reject } = requests.get(msg.id);
    requests.delete(msg.id);
    if (msg.success) resolve(msg.result);
    else reject({ code: 'E_HA_REQUEST', message: msg.error?.message || 'Home Assistant rechazó la petición.' });
  }

  function failAuth() {
    const error = { code: 'E_HA_AUTH', message: 'Token de Home Assistant inválido. Revisa la configuración del Estudio.' };
    if (settleConnect) { const done = settleConnect; teardown(); done(error); } else notifyAll(error);
  }

  // Home Assistant sends each pipeline event as { type, data, timestamp }.
  function dispatchEvent(id, envelope) {
    const pipeline = pipelines.get(id);
    if (!pipeline) return;
    const h = pipeline.handlers;
    const event = envelope.data || {};
    switch (envelope.type) {
      case 'run-start': return flushAudioStart(pipeline, event);
      case 'stt-end': return h.onHeard?.(event.stt_output?.text ?? '');
      case 'intent-end': return h.onAnswer?.(event.intent_output?.response?.speech?.plain?.speech ?? '');
      case 'tts-end': return h.onAudio?.(event.tts_output?.url || ''); // relative: serve.py proxies it (same origin)
      case 'error': return h.onError?.({ code: event.code ?? 'E_ASSIST', message: event.message ?? 'Falló el pipeline de voz.' });
      case 'run-end': h.onDone?.(); return pipelines.delete(id);
      default: return undefined;
    }
  }

  function flushAudioStart(pipeline, event) {
    const state = pipeline.audioState;
    if (!state) return;
    state.binaryHandlerId = event.runner_data?.stt_binary_handler_id ?? null;
    if (state.binaryHandlerId == null) return;
    const pending = state.pending;
    state.pending = [];
    for (const item of pending) sendBinaryFrame(state.binaryHandlerId, item.kind === 'chunk' ? item.int16 : null);
  }

  function sendBinaryFrame(handlerId, int16) {
    const pcm = int16 ? new Uint8Array(int16.buffer, int16.byteOffset, int16.byteLength) : new Uint8Array(0);
    const frame = new Uint8Array(1 + pcm.length);
    frame[0] = handlerId;
    frame.set(pcm, 1);
    ws.send(frame);
  }

  function handleDrop() {
    if (!authenticated) {
      if (settleConnect) { const done = settleConnect; teardown(); done(downError()); }
      return;
    }
    notifyAll({ code: 'E_HA_DOWN', message: 'Se perdió la conexión con Home Assistant. ¿Está arrancado el stack?' });
    teardown();
  }

  const notifyAll = (error) => {
    for (const pipeline of pipelines.values()) pipeline.handlers.onError?.(error);
    for (const pending of requests.values()) pending.reject(error);
    pipelines.clear();
    requests.clear();
  };

  function teardown() {
    authenticated = false;
    if (!ws) return;
    try { ws.onmessage = null; ws.onerror = null; ws.onclose = null; ws.close(); } catch (err) { console.warn('ha-assist: error al cerrar el WebSocket', err); }
    ws = null;
  }

  const downError = () => ({ code: 'E_HA_DOWN', message: `No conecta con Home Assistant en ${base}. ¿Está arrancado el stack?` });

  return { connect, runText, startAudio, request, close };
}
