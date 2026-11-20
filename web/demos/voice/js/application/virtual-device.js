// Virtual device: publishes MQTT discovery, availability and state; applies commands.
// createVirtualDevice({ catalog, bus, onChange }) -> { start, command, report, getState, stop }.
// report(deviceId, key, value) is a simulated physical reading (sensor, door, motion).

import { buildDiscovery } from '../domain/discovery.js';
import { stateTopic, availabilityTopic } from '../domain/topics.js';
import { initialState, parseCommandTopic, applyCommand, applyReading } from '../domain/device-state.js';

export function createVirtualDevice({ catalog, bus, onChange } = {}) {
  if (!catalog || !bus) {
    throw new TypeError('createVirtualDevice: catalog y bus son obligatorios');
  }
  const base = catalog.base_topic;
  let state = initialState(catalog);
  let started = false;

  async function start() {
    if (started) return;
    for (const message of buildDiscovery(catalog)) {
      bus.publish(message.topic, message.payload, { retain: message.retain });
    }
    for (const device of catalog.devices) {
      bus.publish(availabilityTopic(base, device.id), 'online', { retain: true });
      publishInitialState(device);
    }
    bus.subscribe(`${base}/+/+/set`, (topic, payload) => handleSet(topic, payload));
    started = true;
  }

  function publishInitialState(device) {
    for (const entity of device.entities) {
      const value = state[device.id]?.[entity.key];
      if (entity.component === 'button' || value === null || value === undefined) continue;
      bus.publish(stateTopic(base, device.id, entity.key), String(value), { retain: true });
    }
  }

  function handleSet(topic, payload) {
    const parsed = parseCommandTopic(base, topic);
    if (!parsed) return null;
    return applyAndPublish(parsed.deviceId, parsed.key, payload);
  }

  function command(deviceId, key, payload) {
    return applyAndPublish(deviceId, key, payload);
  }

  function report(deviceId, key, value) {
    return publishResult(deviceId, key, applyReading(state, catalog, deviceId, key, value));
  }

  function applyAndPublish(deviceId, key, payload) {
    return publishResult(deviceId, key, applyCommand(state, catalog, deviceId, key, payload));
  }

  function publishResult(deviceId, key, result) {
    state = result.state;
    const event = result.event ?? { type: 'error', deviceId, key, code: 'E_UNKNOWN' };
    if (event.type === 'changed') {
      const value = state[deviceId]?.[key];
      bus.publish(stateTopic(base, deviceId, key), String(value ?? ''), { retain: true });
    }
    if (typeof onChange === 'function') onChange(state, event);
    return event;
  }

  function getState() {
    return state;
  }

  function stop() {
    if (!started) return;
    for (const device of catalog.devices) {
      bus.publish(availabilityTopic(base, device.id), 'offline', { retain: true });
    }
    started = false;
  }

  return { start, command, report, getState, stop };
}
