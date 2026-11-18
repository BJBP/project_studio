// Runs the simulated sensors: drifting readings on a timer, and "pulse" for tests (door opens 5 s, a loud bang…).
// createSimulator({ catalog, virtualDevice, timers? }) -> { start, stop, pulse(deviceId, key, seconds?) }.
import { nextReading, testValues } from '../domain/simulation.js';

const DEFAULT_PULSE_S = 5;

export function createSimulator({ catalog, virtualDevice, timers = globalThis }) {
  const handles = new Set();
  const entities = (catalog.devices ?? []).flatMap((device) =>
    (device.entities ?? []).map((entity) => ({ device, entity })));

  function start() {
    for (const { device, entity } of entities) {
      if (entity.sim?.type !== 'drift') continue;
      const tick = () => {
        const current = virtualDevice.getState()[device.id]?.[entity.key];
        virtualDevice.report(device.id, entity.key, nextReading(entity.sim, current));
      };
      tick();
      handles.add(timers.setInterval(tick, (entity.sim.every_s ?? 10) * 1000));
    }
  }

  function pulse(deviceId, key, seconds) {
    const found = entities.find(({ device, entity }) => device.id === deviceId && entity.key === key);
    if (!found) return { code: 'E_UNKNOWN_ENTITY' };
    const { on, off } = testValues(found.entity);
    virtualDevice.report(deviceId, key, on);
    const handle = timers.setTimeout(() => {
      handles.delete(handle);
      virtualDevice.report(deviceId, key, off);
    }, (seconds ?? found.entity.sim?.pulse_s ?? DEFAULT_PULSE_S) * 1000);
    handles.add(handle);
    return null;
  }

  function stop() {
    for (const handle of handles) { timers.clearInterval(handle); timers.clearTimeout(handle); }
    handles.clear();
  }

  return { start, stop, pulse };
}
