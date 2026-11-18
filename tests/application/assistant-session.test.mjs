// Tests for the assistant session: sendText -> onAnswer + speaker.play; audio path states.
// Assist, mic and speaker are fakes; no network and no DOM.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createAssistantSession } from '../../web/demos/voice/js/application/assistant-session.js';

function createFakes() {
  const played = [];
  const statuses = [];
  const answers = [];
  const errors = [];
  let audioHandlers = null;
  let runHandlers = null;
  const assist = {
    connect: async () => {},
    startAudio(handlers) {
      audioHandlers = handlers;
      return { sendChunk() {}, end() {} };
    },
    runText(text, handlers) {
      runHandlers = handlers;
      return 1;
    },
    close() {},
  };
  const mic = { start: async () => {}, stop() {} };
  const speaker = {
    play: async (url) => { played.push(url); },
    setVolume() {},
    stop() {},
  };
  const handlers = {
    onStatus: (key) => statuses.push(key),
    onHeard: () => {},
    onAnswer: (text) => answers.push(text),
    onLevel: () => {},
    onError: (error) => errors.push(error),
  };
  return {
    assist, mic, speaker, handlers, played, statuses, answers, errors,
    getAudioHandlers: () => audioHandlers,
    getRunHandlers: () => runHandlers,
  };
}

test('sendText routes the answer to onAnswer and plays the TTS audio', async () => {
  const fakes = createFakes();
  const session = createAssistantSession(fakes);

  session.sendText('enciende el foco');
  assert.deepEqual(fakes.statuses, ['thinking']);

  fakes.getRunHandlers().onAnswer('Encendido.');
  fakes.getRunHandlers().onAudio('http://ha.local/api/tts/reply.mp3');
  fakes.getRunHandlers().onDone();
  await new Promise((resolve) => setImmediate(resolve));

  assert.deepEqual(fakes.answers, ['Encendido.']);
  assert.deepEqual(fakes.played, ['http://ha.local/api/tts/reply.mp3']);
  assert.deepEqual(fakes.errors, []);
  assert.deepEqual(fakes.statuses, ['thinking', 'speaking', 'idle']);
});

test('sendText with empty text reports an error and does not call assist', () => {
  const fakes = createFakes();
  const session = createAssistantSession(fakes);

  session.sendText('   ');

  assert.equal(fakes.getRunHandlers(), null);
  assert.equal(fakes.errors[0]?.code, 'E_EMPTY_INPUT');
});

test('startTalking/stopTalking manage status listening -> thinking', async () => {
  const fakes = createFakes();
  const session = createAssistantSession(fakes);

  await session.startTalking();
  assert.deepEqual(fakes.statuses, ['listening']);
  session.stopTalking();
  assert.deepEqual(fakes.statuses, ['listening', 'thinking']);
});
