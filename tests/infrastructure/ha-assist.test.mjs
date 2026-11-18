// Tests for ha-assist.js message logic using an injectable fake WebSocket.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createAssist } from '../../web/demos/voice/js/infrastructure/ha-assist.js';

class FakeWebSocket {
  static instances = [];

  constructor(url) {
    this.url = url;
    this.sent = [];
    this.onmessage = null;
    this.onerror = null;
    this.onclose = null;
    FakeWebSocket.instances.push(this);
  }

  send(data) {
    this.sent.push(data);
  }

  close() {
    const onclose = this.onclose;
    if (onclose) onclose();
  }

  receive(message) {
    const text = typeof message === 'string' ? message : JSON.stringify(message);
    if (this.onmessage) this.onmessage({ data: text });
  }

  fail() {
    if (this.onerror) this.onerror(new Error('connection failed'));
  }

  sentJson(index) {
    return JSON.parse(this.sent[index]);
  }
}

const HA_URL = 'http://ha.test:8124';

async function connectedAssist(handlers = {}) {
  FakeWebSocket.instances = [];
  const assist = createAssist({ haUrl: HA_URL, token: 'tok123', WebSocketImpl: FakeWebSocket });
  const pending = assist.connect();
  const ws = FakeWebSocket.instances[0];
  ws.receive({ type: 'auth_required' });
  ws.receive({ type: 'auth_ok' });
  await pending;
  return { assist, ws, handlers };
}

test('connect() converts http->ws, authenticates and resolves on auth_ok', async () => {
  FakeWebSocket.instances = [];
  const assist = createAssist({ haUrl: HA_URL, token: 'tok123', WebSocketImpl: FakeWebSocket });
  const pending = assist.connect();
  const ws = FakeWebSocket.instances[0];
  assert.equal(ws.url, 'ws://ha.test:8124/api/websocket');
  ws.receive({ type: 'auth_required' });
  assert.deepEqual(ws.sentJson(0), { type: 'auth', access_token: 'tok123' });
  ws.receive({ type: 'auth_ok' });
  await pending;
  assist.close();
});

test('connect() rejects with E_HA_AUTH on auth_invalid', async () => {
  FakeWebSocket.instances = [];
  const assist = createAssist({ haUrl: HA_URL, token: 'bad', WebSocketImpl: FakeWebSocket });
  const pending = assist.connect();
  const ws = FakeWebSocket.instances[0];
  ws.receive({ type: 'auth_required' });
  ws.receive({ type: 'auth_invalid', message: 'bad token' });
  await assert.rejects(pending, (err) => err.code === 'E_HA_AUTH');
});

test('connect() rejects with E_HA_DOWN on connection error', async () => {
  FakeWebSocket.instances = [];
  const assist = createAssist({ haUrl: HA_URL, token: 'tok123', WebSocketImpl: FakeWebSocket });
  const pending = assist.connect();
  FakeWebSocket.instances[0].fail();
  await assert.rejects(pending, (err) => err.code === 'E_HA_DOWN');
});

test('runText() sends intent pipeline and dispatches stt/intent/tts/run-end events', async () => {
  const { assist, ws } = await connectedAssist();
  const heard = [];
  const answers = [];
  const audioUrls = [];
  let done = false;
  assist.runText('enciende el foco', {
    onHeard: (text) => heard.push(text),
    onAnswer: (text) => answers.push(text),
    onAudio: (url) => audioUrls.push(url),
    onDone: () => { done = true; },
  });
  const command = ws.sentJson(ws.sent.length - 1);
  assert.equal(command.type, 'assist_pipeline/run');
  assert.equal(command.start_stage, 'intent');
  assert.equal(command.end_stage, 'tts');
  assert.deepEqual(command.input, { text: 'enciende el foco' });
  const id = command.id;

  ws.receive({ id, type: 'event', event: { type: 'stt-end', data: { stt_output: { text: 'enciende el foco' } } } });
  ws.receive({ id, type: 'event', event: { type: 'intent-end', data: { intent_output: { response: { speech: { plain: { speech: 'Hecho.' } } } } } } });
  ws.receive({ id, type: 'event', event: { type: 'tts-end', data: { tts_output: { url: '/api/tts_proxy/abc.mp3' } } } });
  ws.receive({ id, type: 'event', event: { type: 'run-end', data: {} } });

  assert.deepEqual(heard, ['enciende el foco']);
  assert.deepEqual(answers, ['Hecho.']);
  assert.deepEqual(audioUrls, ['http://ha.test:8124/api/tts_proxy/abc.mp3']);
  assert.equal(done, true);
  assist.close();
});

test('runText() keeps absolute TTS URLs unchanged', async () => {
  const { assist, ws } = await connectedAssist();
  const urls = [];
  assist.runText('hola', { onAudio: (url) => urls.push(url) });
  const { id } = ws.sentJson(ws.sent.length - 1);
  ws.receive({ id, type: 'event', event: { type: 'tts-end', data: { tts_output: { url: 'http://cdn.test/tts.mp3' } } } });
  assert.deepEqual(urls, ['http://cdn.test/tts.mp3']);
  assist.close();
});

test('startAudio() sends stt pipeline; sendChunk frames binary with handler id; end() sends the bare id', async () => {
  const { assist, ws } = await connectedAssist();
  const handle = assist.startAudio({});
  const command = ws.sentJson(ws.sent.length - 1);
  assert.equal(command.start_stage, 'stt');
  assert.equal(command.end_stage, 'tts');
  assert.deepEqual(command.input, { sample_rate: 16000 });
  const id = command.id;

  ws.receive({ id, type: 'event', event: { type: 'run-start', data: { runner_data: { stt_binary_handler_id: 7 } } } });
  const pcm = new Int16Array([1, -2, 32767]);
  handle.sendChunk(pcm);
  const frame = ws.sent[ws.sent.length - 1];
  assert.ok(frame instanceof Uint8Array);
  assert.equal(frame.length, 1 + pcm.byteLength);
  assert.equal(frame[0], 7);
  assert.deepEqual(Array.from(new Uint8Array(frame.buffer, frame.byteOffset + 1, pcm.byteLength)), Array.from(new Uint8Array(pcm.buffer)));
  handle.end();
  const endFrame = ws.sent[ws.sent.length - 1];
  assert.deepEqual(Array.from(endFrame), [7]);
  assist.close();
});

test('startAudio() queues chunks and end sent before run-start', async () => {
  const { assist, ws } = await connectedAssist();
  const handle = assist.startAudio({});
  handle.sendChunk(new Int16Array([10, 20]));
  handle.end();
  const sentBefore = ws.sent.length;
  const { id } = ws.sentJson(ws.sent.length - 1);
  ws.receive({ id, type: 'event', event: { type: 'run-start', data: { runner_data: { stt_binary_handler_id: 3 } } } });
  assert.equal(ws.sent.length, sentBefore + 2);
  assert.equal(ws.sent[sentBefore][0], 3);
  assert.deepEqual(Array.from(ws.sent[sentBefore + 1]), [3]);
  assist.close();
});

test('error events are routed to onError with code and message', async () => {
  const { assist, ws } = await connectedAssist();
  const errors = [];
  assist.runText('hola', { onError: (err) => errors.push(err) });
  const { id } = ws.sentJson(ws.sent.length - 1);
  ws.receive({ id, type: 'event', event: { type: 'error', data: { code: 'stt-no-text', message: 'No se entendió.' } } });
  assert.deepEqual(errors, [{ code: 'stt-no-text', message: 'No se entendió.' }]);
  assist.close();
});
