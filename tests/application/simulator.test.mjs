import test from 'node:test';
import assert from 'node:assert/strict';
import { createSimulator } from '../../web/demos/voice/js/application/simulator.js';

test('pulse sets the test value and goes back after its time', () => {
  const reports = [];
  const pending = [];
  const timers = { setTimeout: (fn) => { pending.push(fn); return pending.length; }, clearTimeout() {}, setInterval() {}, clearInterval() {} };
  const catalog = { devices: [{ id: 'e', entities: [{ key: 'door', component: 'binary_sensor', sim: { pulse_s: 2 } }] }] };
  const sim = createSimulator({ catalog, timers, virtualDevice: { report: (...a) => reports.push(a), getState: () => ({}) } });
  assert.equal(sim.pulse('e', 'door'), null);
  pending[0]();
  assert.deepEqual(reports, [['e', 'door', 'ON'], ['e', 'door', 'OFF']]);
  assert.equal(sim.pulse('e', 'nope').code, 'E_UNKNOWN_ENTITY');
});
