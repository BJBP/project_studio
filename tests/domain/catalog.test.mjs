import test from "node:test";
import assert from "node:assert/strict";
import { validateCatalog } from "../../web/demos/voice/js/domain/catalog.js";

const valid = () => ({
  base_topic: "studio",
  devices: [
    {
      id: "circuito_maestro",
      name: "Circuito maestro",
      model: "ESP32-S3 (virtual)",
      area: "Taller",
      entities: [
        { key: "foco", component: "switch", name: "Foco" },
        { key: "mic", component: "sensor", name: "Micro", unit: "dB" },
      ],
    },
  ],
});

test("accepts a valid catalog", () => {
  assert.deepEqual(validateCatalog(valid()), { ok: true });
});

test("rejects an empty device list with E_NO_DEVICES", () => {
  const result = validateCatalog({ devices: [] });
  assert.equal(result.ok, false);
  assert.equal(result.errors[0].code, "E_NO_DEVICES");
});

test("rejects a bad device id and duplicate ids", () => {
  const data = valid();
  data.devices[0].id = "Circuito Maestro!";
  const bad = validateCatalog(data);
  assert.equal(bad.ok, false);
  assert.ok(bad.errors.some((e) => e.code === "E_DEVICE_ID"));

  const dup = valid();
  dup.devices.push({ ...structuredClone(dup.devices[0]) });
  const dupResult = validateCatalog(dup);
  assert.ok(dupResult.errors.some((e) => e.code === "E_DUPLICATE_ID"));
});

test("rejects bad key, component and missing names", () => {
  const data = valid();
  data.devices[0].entities = [
    { key: "Bad Key", component: "switch", name: "Foco" },
    { key: "ok_key", component: "lamp", name: "Lámpara" },
    { key: "no_name", component: "text" },
  ];
  const result = validateCatalog(data);
  const codes = result.errors.map((e) => e.code);
  assert.ok(codes.includes("E_ENTITY_KEY"));
  assert.ok(codes.includes("E_COMPONENT"));
  assert.ok(codes.includes("E_NAME"));
});
