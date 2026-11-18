import test from 'node:test';
import assert from 'node:assert/strict';
import { createBrainChoice } from '../../web/demos/voice/js/application/brain-choice.js';

const providers = [
  { id: 'local', label: 'Local', cloud: false, pipeline: 'A local' },
  { id: 'claude', label: 'Claude', cloud: true, hasKey: false, pipeline: 'A Claude' },
];

function setup({ pipelines = [{ id: 'p1', name: 'A local' }], saved = null, saveKey } = {}) {
  const calls = { pipeline: [], stored: [] };
  const assist = { request: async () => ({ pipelines }) };
  const session = { setPipeline: (id) => calls.pipeline.push(id) };
  const store = { get: () => saved, set: (id) => calls.stored.push(id) };
  return { calls, choice: createBrainChoice({ assist, session, providers, saveKey, store }), pipelines };
}

test('load selects the local AI and tells the session which pipeline to use', async () => {
  const { calls, choice } = setup();
  await choice.load();
  assert.equal(choice.current.id, 'local');
  assert.deepEqual(calls.pipeline, ['p1']);
});

test('addKey reloads and the cloud AI becomes selectable; failing falls back to local', async () => {
  const pipelines = [{ id: 'p1', name: 'A local' }];
  const { calls, choice } = setup({ pipelines, saveKey: async () => { pipelines.push({ id: 'p2', name: 'A Claude' }); return { ok: true }; } });
  await choice.load();
  assert.equal(choice.brains[1].status, 'needs_key');
  assert.equal((await choice.addKey('claude', 'k')).ok, true);
  choice.select('claude');
  assert.equal(choice.current.id, 'claude');
  assert.deepEqual(calls.stored, ['claude']);
  assert.equal(choice.fallBackToLocal(), true);
  assert.equal(choice.current.id, 'local');
  assert.equal(choice.fallBackToLocal(), false);
});

test('a rejected key changes nothing', async () => {
  const { choice } = setup({ saveKey: async () => ({ ok: false, code: 'E_FLOW_INVALID' }) });
  await choice.load();
  assert.equal((await choice.addKey('claude', 'bad')).code, 'E_FLOW_INVALID');
  assert.equal(choice.brains[1].status, 'needs_key');
});
