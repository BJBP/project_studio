// Builds the OLED text model from device state and the last answer.
// oledFromState(deviceState, answerText) -> { header, lines } via oledLayout.

import { oledLayout } from '../domain/oled.js';

const HEADER_SWITCHES = [
  { key: 'foco', label: 'FOCO' },
  { key: 'cooler', label: 'FAN' },
];
const DEFAULT_BODY = 'Listo. Di una orden';

export function oledFromState(deviceState, answerText) {
  const firstDeviceId = deviceState ? Object.keys(deviceState)[0] : null;
  const firstDevice = firstDeviceId ? deviceState[firstDeviceId] : {};
  const header = HEADER_SWITCHES
    .map(({ key, label }) => `${label}:${normalizeSwitch(firstDevice?.[key])}`)
    .join('  ');
  const body = String(answerText ?? '').trim() || DEFAULT_BODY;
  return oledLayout({ header, body });
}

function normalizeSwitch(value) {
  return String(value ?? 'OFF').toUpperCase() === 'ON' ? 'ON' : 'OFF';
}
