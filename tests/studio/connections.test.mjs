// External connections block rules: ids, sharing a device, the shareable list and the row summary.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { agoParts, draft, remoteIdFor, share, shareable, summary } from '../../web/studio/js/connections.js';

const connector = { type: 'demo_mqtt', options: [{ key: 'host', default: '127.0.0.1' }, { key: 'port', default: 1883 }] };

test('a new connection gets a free id and the connector defaults', () => {
  const conn = draft(connector, 'Panel de Prueba', ['panel-de-prueba']);
  assert.equal(conn.id, 'panel-de-prueba-2');
  assert.deepEqual(conn.options, { host: '127.0.0.1', port: 1883 });
});

test('sharing a device suggests its remote id and only sends', () => {
  const conn = share(draft(connector, 'x'), 'switch.circuito_maestro_foco', true);
  assert.deepEqual(conn.devices, [{ entity_id: 'switch.circuito_maestro_foco', remote_id: 'circuito-maestro-foco', direction: 'send' }]);
  assert.deepEqual(share(conn, 'switch.circuito_maestro_foco', false).devices, []);
  assert.equal(remoteIdFor('sensor.salón_temperatura'), 'salon-temperatura');
});

test('only devices a platform can use are listed, by name', () => {
  const states = [{ entity_id: 'switch.b', attributes: { friendly_name: 'B' } }, { entity_id: 'tts.piper', attributes: {} },
    { entity_id: 'light.a', attributes: { friendly_name: 'A' } }];
  assert.deepEqual(shareable(states).map((s) => s.entity_id), ['light.a', 'switch.b']);
});

test('the row says paused, waiting, error or how long ago it sent', () => {
  const conn = { enabled: true, devices: [{}] };
  assert.equal(summary({ ...conn, enabled: false }, null, 0).state, 'paused');
  assert.equal(summary({ ...conn, devices: [] }, null, 0).reason, 'noDevices');
  assert.equal(summary(conn, { state: 'error', message: 'E_CONN_DOWN' }, 0).message, 'E_CONN_DOWN');
  assert.deepEqual(summary(conn, { state: 'connected', sent_at: 100 }, 103), { state: 'ok', ago: 3, quiet: false });
});

test('time ago is read in seconds, minutes or hours', () => {
  assert.deepEqual([agoParts(5), agoParts(653), agoParts(7200)], [['s', 5], ['min', 11], ['h', 2]]);
});
