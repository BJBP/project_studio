import test from 'node:test';
import assert from 'node:assert/strict';
import { nextReading, testValues } from '../../web/demos/voice/js/domain/simulation.js';
import { applyCommand, applyReading, initialState } from '../../web/demos/voice/js/domain/device-state.js';
import { buildDiscovery } from '../../web/demos/voice/js/domain/discovery.js';

const catalog = { base_topic: 's', devices: [{ id: 'e', name: 'E', entities: [
  { key: 'door', component: 'binary_sensor', name: 'Puerta', device_class: 'door' },
  { key: 'temp', component: 'sensor', name: 'T', sim: { type: 'drift', min: 20, max: 30, rest: 24, step: 1 } },
  { key: 'lock', component: 'lock', name: 'L' },
] }] };

test('drift stays inside its range and manual sims do not move', () => {
  assert.equal(nextReading(catalog.devices[0].entities[1].sim, 30, () => 1), 30);
  assert.equal(nextReading(catalog.devices[0].entities[1].sim, 20, () => 0), 20);
  assert.equal(nextReading({ type: 'manual' }, 5), 5);
  assert.deepEqual(testValues(catalog.devices[0].entities[0]), { on: 'ON', off: 'OFF' });
});

test('readings and the lock change state; commands cannot fake a sensor', () => {
  let state = initialState(catalog);
  assert.deepEqual(state.e, { door: 'OFF', temp: 24, lock: 'LOCKED' });
  state = applyReading(state, catalog, 'e', 'door', 'ON').state;
  assert.equal(state.e.door, 'ON');
  assert.equal(applyReading(state, catalog, 'e', 'lock', 'X').event.code, 'E_NOT_A_SENSOR');
  assert.equal(applyCommand(state, catalog, 'e', 'lock', 'UNLOCK').state.e.lock, 'UNLOCKED');
  assert.equal(applyCommand(state, catalog, 'e', 'door', 'ON').event.code, 'E_UNKNOWN_ENTITY');
});

test('discovery gives stable ids, device classes and lock payloads', () => {
  const [door, , lock] = buildDiscovery(catalog);
  assert.equal(door.payload.default_entity_id, 'binary_sensor.e_door');
  assert.equal(door.payload.device_class, 'door');
  assert.equal(lock.payload.state_locked, 'LOCKED');
});
