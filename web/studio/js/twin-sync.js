// Digital twin translation, pure. twinMessage(states, deviceId, view) -> the 'studio-device' message for the 3D
// circuit; twinAction(part, deviceId, view, states) -> the Home Assistant service call for a click (or null).
// view = { source: 'real'|'virtual', load: 'bulb'|'fan' (what relay 1 drives), header? (OLED top line) }.
// Entity ids follow device_names.py: with a real board, real = <device>_<key> and virtual = <device>_virtual_<key>;
// without one, the virtual is plain. With the board on the cable (no Wi-Fi), its stand-in is <device>_cable_<key>
// (firmware/cable_bridge.py) and takes the real board's place; message.link says which: 'wifi' | 'cable' | null.
import { oledLayout } from '../../demos/voice/js/domain/oled.js';

const RELAY_KEY = 'foco';      // relay 1 in the catalog (its name is chosen in «Qué hay conectado»)
const SECOND_KEY = 'cooler';   // relay 2
const OFFLINE = new Set(['unavailable', 'unknown']);

export function hasRealBoard(states, deviceId) {
  return states.some((s) => s.entity_id.includes(`.${deviceId}_virtual_`));
}

const stateOf = (states, id) => states.find((s) => s.entity_id === id);
const usable = (state) => Boolean(state) && !OFFLINE.has(state.state);

// 'wifi' | 'cable' | null: how the real board answers now (Wi-Fi first).
export function realLink(states, deviceId) {
  if (usable(stateOf(states, `switch.${deviceId}_${RELAY_KEY}`)) && hasRealBoard(states, deviceId)) return 'wifi';
  return usable(stateOf(states, `switch.${deviceId}_cable_${RELAY_KEY}`)) ? 'cable' : null;
}

function entityId(domain, key, deviceId, view, states) {
  if (view.source === 'virtual') return `${domain}.${deviceId}_${hasRealBoard(states, deviceId) ? 'virtual_' : ''}${key}`;
  return `${domain}.${deviceId}_${realLink(states, deviceId) === 'cable' ? 'cable_' : ''}${key}`;
}

export function twinMessage(states, deviceId, view) {
  const pick = (domain, key) => stateOf(states, entityId(domain, key, deviceId, view, states));
  const relay = pick('switch', RELAY_KEY);
  const second = pick('switch', SECOND_KEY);
  const relayOn = relay?.state === 'on';
  const secondOn = second?.state === 'on';
  const oled = oledLayout({ header: '', body: pick('text', 'oled')?.state ?? '' });
  return {
    type: 'studio-device',
    foco: view.load === 'fan' ? secondOn : relayOn,
    cooler: view.load === 'fan' ? relayOn : secondOn,
    oledHeader: view.header ?? '',
    oledLines: oled.lines,
    online: view.source === 'virtual' ? usable(relay) : realLink(states, deviceId) !== null,
    link: view.source === 'virtual' ? null : realLink(states, deviceId),
    alarmStamp: pick('button', 'alarma')?.state ?? null,
  };
}

export function twinAction(part, deviceId, view, states) {
  if (part === 'buzzer') return { domain: 'button', service: 'press', entity_id: entityId('button', 'alarma', deviceId, view, states) };
  const relayPart = view.load === 'fan' ? 'fan' : 'bulb';
  const key = part === 'relay' || part === relayPart ? RELAY_KEY : part === 'bulb' || part === 'fan' ? SECOND_KEY : null;
  return key ? { domain: 'switch', service: 'toggle', entity_id: entityId('switch', key, deviceId, view, states) } : null;
}
