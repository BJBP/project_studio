// External connections block rules, pure: a new connection from a connector, the remote id suggested for an entity,
// sharing a device or not, and what a row says. summary(conn, status, nowS) -> { state: ok|error|paused|waiting, ... }.
export const SHAREABLE = ['switch', 'light', 'fan', 'lock', 'cover', 'sensor', 'binary_sensor', 'input_boolean'];
const RECENT_S = 120;

export const slug = (text) => text.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
  .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 63) || 'conexion';

export function remoteIdFor(entityId) {
  return slug(entityId.split('.').slice(1).join('.'));
}

export function uniqueId(name, taken = []) {
  let id = slug(name);
  for (let n = 2; taken.includes(id); n += 1) id = `${slug(name)}-${n}`;
  return id;
}

export function draft(connector, name, taken = []) {
  const options = Object.fromEntries((connector.options ?? []).map((o) => [o.key, o.default ?? '']));
  return { id: uniqueId(name, taken), name, type: connector.type, enabled: true, options, devices: [] };
}

export function share(conn, entityId, on) {
  const devices = conn.devices.filter((d) => d.entity_id !== entityId);
  if (on) devices.push({ entity_id: entityId, remote_id: remoteIdFor(entityId), direction: 'send' });
  return { ...conn, devices };
}

export function shareable(states) {
  return states.filter((s) => SHAREABLE.includes(s.entity_id.split('.')[0]))
    .map((s) => ({ entity_id: s.entity_id, name: s.attributes?.friendly_name ?? s.entity_id }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

export function summary(conn, status, nowS) {
  if (!conn.enabled) return { state: 'paused' };
  if (!conn.devices.length) return { state: 'waiting', reason: 'noDevices' };
  if (!status) return { state: 'waiting', reason: 'starting' };
  if (status.state === 'error') return { state: 'error', message: status.message };
  if (status.state !== 'connected') return { state: 'waiting', reason: 'starting' };
  const ago = status.sent_at ? Math.max(0, Math.round(nowS - status.sent_at)) : null;
  return { state: 'ok', ago, quiet: ago === null || ago > RECENT_S };
}

// How long ago, in the unit a person reads best: ['s'|'min'|'h', n].
export function agoParts(seconds) {
  if (seconds < 90) return ['s', seconds];
  if (seconds < 5400) return ['min', Math.round(seconds / 60)];
  return ['h', Math.round(seconds / 3600)];
}
