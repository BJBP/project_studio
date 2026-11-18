import test from "node:test";
import assert from "node:assert/strict";
import { buildDiscovery } from "../../web/demos/voice/js/domain/discovery.js";

const catalog = () => ({
  base_topic: "studio",
  devices: [
    {
      id: "circuito_maestro",
      name: "Circuito maestro",
      model: "ESP32-S3 (virtual)",
      area: "Taller",
      entities: [
        { key: "foco", component: "switch", name: "Foco" },
        { key: "alarma", component: "button", name: "Alarma" },
        { key: "oled", component: "text", name: "Pantalla" },
        { key: "mic", component: "sensor", name: "Nivel del micrófono", unit: "dB" },
        { key: "raw", component: "sensor", name: "Sin unidad" },
      ],
    },
  ],
});

test("emits one retained message per entity with the right topic", () => {
  const messages = buildDiscovery(catalog());
  assert.equal(messages.length, 5);
  assert.ok(messages.every((m) => m.retain === true));
  assert.deepEqual(
    messages.map((m) => m.topic),
    [
      "homeassistant/switch/circuito_maestro/foco/config",
      "homeassistant/button/circuito_maestro/alarma/config",
      "homeassistant/text/circuito_maestro/oled/config",
      "homeassistant/sensor/circuito_maestro/mic/config",
      "homeassistant/sensor/circuito_maestro/raw/config",
    ],
  );
});

test("common payload fields and device block are filled in", () => {
  const [foco] = buildDiscovery(catalog());
  assert.equal(foco.payload.unique_id, "circuito_maestro_foco");
  assert.equal(foco.payload.availability_topic, "studio/circuito_maestro/status");
  assert.equal(foco.payload.payload_available, "online");
  assert.equal(foco.payload.payload_not_available, "offline");
  assert.deepEqual(foco.payload.device, {
    identifiers: ["circuito_maestro"],
    name: "Circuito maestro",
    model: "ESP32-S3 (virtual)",
    manufacturer: "Project Studio",
    suggested_area: "Taller",
  });
});

test("component-specific fields follow the spec", () => {
  const [foco, alarma, oled, mic] = buildDiscovery(catalog());
  assert.equal(foco.payload.command_topic, "studio/circuito_maestro/foco/set");
  assert.equal(foco.payload.state_topic, "studio/circuito_maestro/foco/state");
  assert.equal(foco.payload.payload_on, "ON");
  assert.equal(foco.payload.payload_off, "OFF");
  assert.equal(alarma.payload.command_topic, "studio/circuito_maestro/alarma/set");
  assert.equal(alarma.payload.payload_press, "PRESS");
  assert.equal(alarma.payload.state_topic, undefined);
  assert.equal(oled.payload.max, 64);
  assert.equal(oled.payload.mode, "text");
  assert.equal(mic.payload.state_topic, "studio/circuito_maestro/mic/state");
  assert.equal(mic.payload.unit_of_measurement, "dB");
});

test("sensor without unit omits unit_of_measurement and empty catalog yields no messages", () => {
  const messages = buildDiscovery(catalog());
  const raw = messages.find((m) => m.topic.includes("/raw/"));
  assert.equal("unit_of_measurement" in raw.payload, false);
  assert.deepEqual(buildDiscovery({ base_topic: "studio", devices: [] }), []);
});
