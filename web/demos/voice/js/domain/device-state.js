// Holds the initial state of every entity and applies incoming commands.
// Receives the catalog and current state, returns new state plus an event.

export function initialState(catalog) {
  const state = {};
  for (const device of catalog.devices ?? []) {
    const values = {};
    for (const entity of device.entities ?? []) {
      if (entity.component === "switch") values[entity.key] = "OFF";
      else if (entity.component === "text") values[entity.key] = "";
      else if (entity.component === "sensor") values[entity.key] = entity.sim?.rest ?? null;
      else if (entity.component === "binary_sensor") values[entity.key] = "OFF";
      else if (entity.component === "lock") values[entity.key] = "LOCKED";
      // Buttons carry no state.
    }
    state[device.id] = values;
  }
  return state;
}

export function parseCommandTopic(base, topic) {
  const prefix = `${base}/`;
  const suffix = "/set";
  if (typeof topic !== "string" || !topic.startsWith(prefix) || !topic.endsWith(suffix)) {
    return null;
  }
  const middle = topic.slice(prefix.length, topic.length - suffix.length);
  const parts = middle.split("/");
  if (parts.length !== 2 || parts[0] === "" || parts[1] === "") return null;
  return { deviceId: parts[0], key: parts[1] };
}

function findEntity(catalog, deviceId, key) {
  const device = (catalog.devices ?? []).find((d) => d.id === deviceId);
  const entity = device && (device.entities ?? []).find((e) => e.key === key);
  return entity ?? null;
}

export function applyCommand(state, catalog, deviceId, key, payload) {
  const entity = findEntity(catalog, deviceId, key);
  if (!entity) {
    return { state, event: { type: "error", code: "E_UNKNOWN_ENTITY" } };
  }
  if (entity.component === "button") {
    return { state, event: { type: "pressed", deviceId, key } };
  }
  if (entity.component === "switch") {
    if (payload !== "ON" && payload !== "OFF") {
      return { state, event: { type: "error", code: "E_BAD_PAYLOAD" } };
    }
    return {
      state: setValue(state, deviceId, key, payload),
      event: { type: "changed", deviceId, key, value: payload },
    };
  }
  if (entity.component === "text") {
    const max = entity.max ?? 64;
    const value = String(payload ?? "").slice(0, max);
    return {
      state: setValue(state, deviceId, key, value),
      event: { type: "changed", deviceId, key, value },
    };
  }
  if (entity.component === "lock") {
    const next = { LOCK: "LOCKED", UNLOCK: "UNLOCKED" }[payload];
    if (!next) return { state, event: { type: "error", code: "E_BAD_PAYLOAD" } };
    return { state: setValue(state, deviceId, key, next), event: { type: "changed", deviceId, key, value: next } };
  }
  // Sensors are read-only from the command side.
  return { state, event: { type: "error", code: "E_UNKNOWN_ENTITY" } };
}

// A simulated physical reading (door opened, temperature, motion): only sensors and binary sensors take one.
export function applyReading(state, catalog, deviceId, key, value) {
  const entity = findEntity(catalog, deviceId, key);
  if (!entity || (entity.component !== "sensor" && entity.component !== "binary_sensor")) {
    return { state, event: { type: "error", code: "E_NOT_A_SENSOR" } };
  }
  if (entity.component === "binary_sensor" && value !== "ON" && value !== "OFF") {
    return { state, event: { type: "error", code: "E_BAD_PAYLOAD" } };
  }
  return { state: setValue(state, deviceId, key, value), event: { type: "changed", deviceId, key, value } };
}

function setValue(state, deviceId, key, value) {
  return {
    ...state,
    [deviceId]: { ...state[deviceId], [key]: value },
  };
}
