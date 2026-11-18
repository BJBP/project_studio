// Validates a voice-demo device catalog. Receives parsed JSON data, returns
// { ok: true } or { ok: false, errors: [{ code, path, message }] }.
const ID_RE = /^[a-z0-9_]+$/;
const COMPONENTS = new Set(["switch", "button", "text", "sensor", "binary_sensor", "lock"]);

export function validateCatalog(data) {
  const errors = [];
  const err = (code, path, message) => errors.push({ code, path, message });

  const devices = data && Array.isArray(data.devices) ? data.devices : null;
  if (!devices || devices.length === 0) {
    err("E_NO_DEVICES", "devices", "The catalog must list at least one device");
    return { ok: false, errors };
  }

  const seen = new Set();
  devices.forEach((device, i) => {
    const base = `devices[${i}]`;
    const id = device ? device.id : undefined;
    if (typeof id !== "string" || !ID_RE.test(id)) {
      err("E_DEVICE_ID", `${base}.id`, "Device id is missing or is not [a-z0-9_]+");
    } else if (seen.has(id)) {
      err("E_DUPLICATE_ID", `${base}.id`, `Duplicate device id "${id}"`);
    } else {
      seen.add(id);
    }
    if (!device || typeof device.name !== "string" || device.name.trim() === "") {
      err("E_NAME", `${base}.name`, "Device name is missing");
    }
    const entities = device && Array.isArray(device.entities) ? device.entities : [];
    entities.forEach((entity, j) => {
      const path = `${base}.entities[${j}]`;
      const key = entity ? entity.key : undefined;
      if (typeof key !== "string" || !ID_RE.test(key)) {
        err("E_ENTITY_KEY", `${path}.key`, "Entity key is missing or is not [a-z0-9_]+");
      }
      if (!entity || !COMPONENTS.has(entity.component)) {
        err("E_COMPONENT", `${path}.component`, "Component must be switch|button|text|sensor|binary_sensor|lock");
      }
      if (!entity || typeof entity.name !== "string" || entity.name.trim() === "") {
        err("E_NAME", `${path}.name`, "Entity name is missing");
      }
    });
  });

  return errors.length === 0 ? { ok: true } : { ok: false, errors };
}
