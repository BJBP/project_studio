import test from 'node:test';
import assert from 'node:assert/strict';
import { syncAliases } from '../../web/demos/voice/js/application/sync-aliases.js';

const catalog = { devices: [{ id: 'dev', entities: [{ key: 'foco', name: 'Foco' }, { key: 'fan', name: 'Ventilador' }] }] };

test('adds missing short names and stable ids; skips what is already right', async () => {
  const sent = [];
  const registry = [
    { entity_id: 'switch.taller_dev_foco', unique_id: 'dev_foco', platform: 'mqtt', aliases: ['Luz'] },
    { entity_id: 'switch.dev_fan', unique_id: 'dev_fan', platform: 'mqtt', aliases: ['Ventilador'] },
    { entity_id: 'switch.other', unique_id: 'dev_foco', platform: 'template', aliases: [] },
  ];
  const assist = { request: async (cmd) => { sent.push(cmd); return cmd.type.endsWith('list') ? registry : null; } };
  assert.equal(await syncAliases({ assist, catalog }), 1);
  assert.deepEqual(sent[1], { type: 'config/entity_registry/update', entity_id: 'switch.taller_dev_foco',
    aliases: ['Luz', 'Foco'], new_entity_id: 'switch.dev_foco' });
  assert.equal(sent.length, 2);
});

test('one failing entity does not stop the others', async () => {
  const registry = [
    { entity_id: 'switch.a', unique_id: 'dev_foco', platform: 'mqtt', aliases: [] },
    { entity_id: 'switch.b', unique_id: 'dev_fan', platform: 'mqtt', aliases: [] },
  ];
  const assist = { request: async (cmd) => {
    if (cmd.type.endsWith('list')) return registry;
    if (cmd.entity_id === 'switch.a') throw { code: 'E_HA_REQUEST' };
    return null;
  } };
  const warn = console.warn;
  console.warn = () => {};
  assert.equal(await syncAliases({ assist, catalog }), 1);
  console.warn = warn;
});
