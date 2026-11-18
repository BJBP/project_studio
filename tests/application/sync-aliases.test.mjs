import test from 'node:test';
import assert from 'node:assert/strict';
import { syncAliases } from '../../web/demos/voice/js/application/sync-aliases.js';

const catalog = { devices: [{ id: 'dev', entities: [{ key: 'foco', name: 'Foco' }, { key: 'fan', name: 'Ventilador' }] }] };

test('adds the missing short names and skips entities that already have them', async () => {
  const sent = [];
  const registry = [
    { entity_id: 'switch.dev_foco', unique_id: 'dev_foco', platform: 'mqtt', aliases: ['Luz'] },
    { entity_id: 'switch.dev_fan', unique_id: 'dev_fan', platform: 'mqtt', aliases: ['Ventilador'] },
    { entity_id: 'switch.other', unique_id: 'dev_foco', platform: 'template', aliases: [] },
  ];
  const assist = { request: async (cmd) => { sent.push(cmd); return cmd.type.endsWith('list') ? registry : null; } };
  assert.equal(await syncAliases({ assist, catalog }), 1);
  assert.deepEqual(sent[1], { type: 'config/entity_registry/update', entity_id: 'switch.dev_foco', aliases: ['Luz', 'Foco'] });
  assert.equal(sent.length, 2);
});
