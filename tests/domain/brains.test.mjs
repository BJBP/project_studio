import test from 'node:test';
import assert from 'node:assert/strict';
import { listBrains, pickBrain } from '../../web/demos/voice/js/domain/brains.js';

const providers = [
  { id: 'local', cloud: false, pipeline: 'Asistente local' },
  { id: 'claude', cloud: true, hasKey: true, pipeline: 'Asistente Claude' },
  { id: 'openai', cloud: true, hasKey: false, pipeline: 'Asistente OpenAI' },
  { id: 'gemini', cloud: true, hasKey: true, pipeline: 'Asistente Gemini' },
];
const pipelines = [{ id: 'p1', name: 'Asistente local' }, { id: 'p2', name: 'Asistente Claude' }];

test('listBrains gives each AI its pipeline and status', () => {
  const brains = listBrains(providers, pipelines);
  assert.deepEqual(brains.map((b) => [b.id, b.pipelineId, b.status]), [
    ['local', 'p1', 'ready'], ['claude', 'p2', 'ready'], ['openai', null, 'needs_key'], ['gemini', null, 'not_ready'],
  ]);
});

test('pickBrain keeps a ready saved choice and otherwise prefers the local AI', () => {
  const brains = listBrains(providers, pipelines);
  assert.equal(pickBrain(brains, 'claude').id, 'claude');
  assert.equal(pickBrain(brains, 'openai').id, 'local');
  assert.equal(pickBrain(brains, null).id, 'local');
  assert.equal(pickBrain([], 'x'), null);
});
