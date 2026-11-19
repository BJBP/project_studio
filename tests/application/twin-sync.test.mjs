// Digital twin: Home Assistant states become the 3D circuit message, and a click becomes the right service call,
// for the real board or its virtual twin, with relay 1 drawn as a bulb or a fan.
import test from 'node:test';
import assert from 'node:assert/strict';
import { twinAction, twinMessage } from '../../web/studio/js/twin-sync.js';

const both = [
  { entity_id: 'switch.lab_foco', state: 'on', attributes: {} },
  { entity_id: 'switch.lab_virtual_foco', state: 'off', attributes: {} },
  { entity_id: 'text.lab_oled', state: 'Hola desde el Estudio', attributes: {} },
  { entity_id: 'button.lab_alarma', state: '2026-11-19T20:00:00', attributes: {} },
];

test('the real board drives the 3D relay as a fan or a bulb', () => {
  const fan = twinMessage(both, 'lab', { source: 'real', load: 'fan', header: 'Lab' });
  assert.equal(fan.cooler, true);
  assert.equal(fan.foco, false);
  assert.equal(fan.online, true);
  assert.deepEqual(fan.oledLines, ['Hola desde el Estudio']);  // 21 characters: one OLED line
  assert.equal(twinMessage(both, 'lab', { source: 'real', load: 'bulb' }).foco, true);
  assert.equal(twinMessage(both, 'lab', { source: 'virtual', load: 'bulb' }).foco, false);
});

test('a board that is not there shows as offline', () => {
  const onlyVirtual = [{ entity_id: 'switch.lab_foco', state: 'on', attributes: {} }];
  assert.equal(twinMessage(onlyVirtual, 'lab', { source: 'real', load: 'bulb' }).online, false);
  assert.equal(twinMessage(onlyVirtual, 'lab', { source: 'virtual', load: 'bulb' }).online, true);
  assert.equal(twinMessage([{ entity_id: 'switch.lab_foco', state: 'unavailable' }, both[1]], 'lab', { source: 'real' }).online, false);
});

test('clicks become service calls on the chosen device', () => {
  assert.deepEqual(twinAction('relay', 'lab', { source: 'real', load: 'fan' }, both),
    { domain: 'switch', service: 'toggle', entity_id: 'switch.lab_foco' });
  assert.equal(twinAction('fan', 'lab', { source: 'virtual', load: 'fan' }, both).entity_id, 'switch.lab_virtual_foco');
  assert.equal(twinAction('bulb', 'lab', { source: 'real', load: 'fan' }, both).entity_id, 'switch.lab_cooler');
  assert.deepEqual(twinAction('buzzer', 'lab', { source: 'real', load: 'bulb' }, both),
    { domain: 'button', service: 'press', entity_id: 'button.lab_alarma' });
  assert.equal(twinAction('oled', 'lab', { source: 'real' }, both), null);
});
