// Tests for oledFromState: header from the first device switches, body from the answer.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { oledFromState } from '../../web/demos/voice/js/application/oled-text.js';
import { initialState } from '../../web/demos/voice/js/domain/device-state.js';

const catalog = JSON.parse(readFileSync(new URL('../../web/demos/voice/data/devices.example.json', import.meta.url)));

test('oledFromState shows FOCO:ON  FAN:OFF when foco is ON', () => {
  const state = initialState(catalog);
  state.circuito_maestro.foco = 'ON';
  const oled = oledFromState(state, 'Foco encendido');

  assert.equal(oled.header, 'FOCO:ON  FAN:OFF');
  assert.ok(oled.lines.join(' ').includes('Foco encendido'));
  assert.ok(oled.header.length <= 21);
  assert.ok(oled.lines.length <= 6);
});

test('oledFromState falls back to the default body when there is no answer', () => {
  const state = initialState(catalog);
  const oled = oledFromState(state, '');

  assert.equal(oled.header, 'FOCO:OFF  FAN:OFF');
  assert.ok(oled.lines.join(' ').includes('Listo. Di una orden'));
});
