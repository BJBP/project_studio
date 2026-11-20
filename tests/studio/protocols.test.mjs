// Protocols block rules: active from Home Assistant's entries or the bridge job, and the "add" link.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { addLink, protocolRows } from '../../web/studio/js/protocols.js';

const catalog = JSON.parse(readFileSync(new URL('../../web/studio/protocols.json', import.meta.url), 'utf8'));

test('a protocol is active when Home Assistant has a loaded entry for its domain', () => {
  const rows = protocolRows(catalog, [{ domain: 'esphome', state: 'loaded' }, { domain: 'knx', state: 'not_loaded' }]);
  const byId = Object.fromEntries(rows.map((r) => [r.id, r.active]));
  assert.equal(byId.esphome, true);
  assert.equal(byId.knx, false);
});

test('a bridge is active while its job runs', () => {
  const rows = protocolRows(catalog, [], { matterbridge: 'running' });
  assert.equal(rows.find((r) => r.bridge === 'matterbridge').active, true);
});

test('every protocol has a domain or a bridge, and the add link opens HA own form', () => {
  assert.ok(catalog.protocols.every((p) => p.domain || p.bridge));
  assert.equal(addLink('http://127.0.0.1:8124/', 'knx'), 'http://127.0.0.1:8124/_my_redirect/config_flow_start?domain=knx');
});
