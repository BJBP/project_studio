// Tests for the virtual device: discovery on start, MQTT command -> state + onChange.
// Uses the real example catalog and a fake bus with real + wildcard matching.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createVirtualDevice } from '../../web/demos/voice/js/application/virtual-device.js';
import { topicMatches } from '../../web/demos/voice/js/infrastructure/mqtt-bus.js';

const catalog = JSON.parse(readFileSync(new URL('../../web/demos/voice/data/devices.example.json', import.meta.url)));

function createFakeBus() {
  const published = [];
  const subscriptions = [];
  return {
    published,
    subscriptions,
    connect: async () => {},
    publish(topic, payload, options) {
      published.push({ topic, payload, retain: Boolean(options?.retain) });
    },
    subscribe(filter, handler) {
      subscriptions.push({ filter, handler });
    },
    close() {},
    emit(topic, payload) {
      for (const { filter, handler } of subscriptions) {
        if (topicMatches(filter, topic)) handler(topic, payload);
      }
    },
  };
}

test('start publishes discovery, availability and initial state', async () => {
  const bus = createFakeBus();
  const device = createVirtualDevice({ catalog, bus, onChange: () => {} });
  await device.start();

  const byTopic = new Map(bus.published.map((entry) => [entry.topic, entry]));
  const entityCount = catalog.devices.reduce((total, d) => total + d.entities.length, 0);
  const discovery = bus.published.filter((entry) => entry.topic.startsWith('homeassistant/'));
  assert.equal(discovery.length, entityCount);
  assert.ok(discovery.every((entry) => entry.retain), 'discovery messages are retained');

  assert.equal(byTopic.get('studio/circuito_maestro/status')?.payload, 'online');
  assert.equal(byTopic.get('studio/circuito_maestro/foco/state')?.payload, 'OFF');
  assert.equal(byTopic.get('studio/circuito_maestro/cooler/state')?.payload, 'OFF');
  assert.equal(byTopic.get('studio/circuito_maestro/oled/state')?.payload, '');
  assert.deepEqual(bus.subscriptions.map((s) => s.filter), ['studio/+/+/set']);

  device.stop();
  assert.equal(byTopic.get('studio/circuito_maestro/status')?.payload, 'online');
  const offline = bus.published.filter((entry) => entry.topic === 'studio/circuito_maestro/status');
  assert.equal(offline.at(-1)?.payload, 'offline');
});

test('MQTT ON command publishes new state and calls onChange', async () => {
  const bus = createFakeBus();
  const events = [];
  const device = createVirtualDevice({ catalog, bus, onChange: (state, event) => events.push({ state, event }) });
  await device.start();
  bus.published.length = 0;

  bus.emit('studio/circuito_maestro/foco/set', 'ON');

  const state = bus.published.find((entry) => entry.topic === 'studio/circuito_maestro/foco/state');
  assert.equal(state?.payload, 'ON');
  assert.equal(state?.retain, true);
  assert.equal(events.length, 1);
  assert.equal(events[0].event.type, 'changed');
  assert.equal(events[0].event.deviceId, 'circuito_maestro');
  assert.equal(events[0].state.circuito_maestro.foco, 'ON');
  device.stop();
});

test('command() works without MQTT transit and also publishes', async () => {
  const bus = createFakeBus();
  const events = [];
  const device = createVirtualDevice({ catalog, bus, onChange: (state, event) => events.push(event) });
  await device.start();
  bus.published.length = 0;

  device.command('circuito_maestro', 'cooler', 'ON');

  const state = bus.published.find((entry) => entry.topic === 'studio/circuito_maestro/cooler/state');
  assert.equal(state?.payload, 'ON');
  assert.deepEqual(events.map((event) => event.type), ['changed']);
  assert.equal(device.getState().circuito_maestro.cooler, 'ON');
  device.stop();
});

test('unknown entity command reports an error and publishes nothing', async () => {
  const bus = createFakeBus();
  const events = [];
  const device = createVirtualDevice({ catalog, bus, onChange: (state, event) => events.push(event) });
  await device.start();
  bus.published.length = 0;

  device.command('circuito_maestro', 'nope', 'ON');

  assert.equal(bus.published.length, 0);
  assert.equal(events[0].type, 'error');
  device.stop();
});
