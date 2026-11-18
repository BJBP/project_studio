import test from "node:test";
import assert from "node:assert/strict";
import {
  initialState,
  parseCommandTopic,
  applyCommand,
} from "../../web/demos/voice/js/domain/device-state.js";

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
        { key: "oled", component: "text", name: "Pantalla", max: 5 },
        { key: "mic", component: "sensor", name: "Micro", unit: "dB" },
      ],
    },
  ],
});

test("initialState seeds switch OFF, text empty, sensor null, button absent", () => {
  const state = initialState(catalog());
  assert.deepEqual(state, {
    circuito_maestro: { foco: "OFF", oled: "", mic: null },
  });
});

test("parseCommandTopic parses valid topics and rejects others", () => {
  assert.deepEqual(parseCommandTopic("studio", "studio/circuito_maestro/foco/set"), {
    deviceId: "circuito_maestro",
    key: "foco",
  });
  assert.equal(parseCommandTopic("studio", "studio/circuito_maestro/foco/state"), null);
  assert.equal(parseCommandTopic("studio", "studio/a/b/c/set"), null);
  assert.equal(parseCommandTopic("studio", "otro/circuito_maestro/foco/set"), null);
});

test("switch commands validate payload and do not mutate the input state", () => {
  const state = initialState(catalog());
  const bad = applyCommand(state, catalog(), "circuito_maestro", "foco", "LOL");
  assert.deepEqual(bad.event, { type: "error", code: "E_BAD_PAYLOAD" });
  assert.equal(bad.state, state);

  const good = applyCommand(state, catalog(), "circuito_maestro", "foco", "ON");
  assert.equal(good.state.circuito_maestro.foco, "ON");
  assert.equal(state.circuito_maestro.foco, "OFF");
  assert.deepEqual(good.event, { type: "changed", deviceId: "circuito_maestro", key: "foco", value: "ON" });
});

test("button press, text truncation and unknown entity", () => {
  const state = initialState(catalog());
  const pressed = applyCommand(state, catalog(), "circuito_maestro", "alarma", "PRESS");
  assert.deepEqual(pressed.event, { type: "pressed", deviceId: "circuito_maestro", key: "alarma" });
  assert.equal(pressed.state, state);

  const text = applyCommand(state, catalog(), "circuito_maestro", "oled", "hola mundo");
  assert.equal(text.state.circuito_maestro.oled, "hola ");
  assert.equal(text.event.value, "hola ");

  const unknown = applyCommand(state, catalog(), "circuito_maestro", "nope", "ON");
  assert.deepEqual(unknown.event, { type: "error", code: "E_UNKNOWN_ENTITY" });
  assert.equal(unknown.state, state);
});
