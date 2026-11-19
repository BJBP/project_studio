// Digital twin translation, pure. twinMessage(states, deviceId, view) -> the 'studio-device' message for the 3D
// circuit; twinAction(part, deviceId, view, states) -> the Home Assistant service call for a click (or null).
// view = { source: 'real'|'virtual', load: 'bulb'|'fan' (what relay 1 drives), header? (OLED top line) }.
// Entity ids follow device_names.py: with a real board, real = <device>_<key> and virtual = <device>_virtual_<key>;
// without one, the virtual is plain.
import { oledLayout } from '../../demos/voice/js/domain/oled.js';

const RELAY_KEY = 'foco';      // relay 1 in the catalog (its name is chosen in «Qué hay conectado»)
const SECOND_KEY = 'cooler';   // relay 2
const OFFLINE = new Set(['unavailable', 'unknown']);

export function hasRealBoard(states, deviceId) {
  return states.some((s) => s.entity_id.includes(`.${deviceId}_virtual_`));
}

function entityId(domain, key, deviceId, view, states) {
  const virtualTwin = view.source === 'virtual' && hasRealBoard(states, deviceId);
  return `${domain}.${deviceId}_${virtualTwin ? 'virtual_' : ''}${key}`;
}

const stateOf = (states, id) => states.find((s) => s.entity_id === id);

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
    online: Boolean(relay) && !OFFLINE.has(relay.state) && (view.source === 'virtual' || hasRealBoard(states, deviceId)),
    alarmStamp: pick('button', 'alarma')?.state ?? null,
  };
}

export function twinAction(part, deviceId, view, states) {
  if (part === 'buzzer') return { domain: 'button', service: 'press', entity_id: entityId('button', 'alarma', deviceId, view, states) };
  const relayPart = view.load === 'fan' ? 'fan' : 'bulb';
  const key = part === 'relay' || part === relayPart ? RELAY_KEY : part === 'bulb' || part === 'fan' ? SECOND_KEY : null;
  return key ? { domain: 'switch', service: 'toggle', entity_id: entityId('switch', key, deviceId, view, states) } : null;
}
