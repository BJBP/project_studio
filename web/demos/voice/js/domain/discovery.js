// Builds Home Assistant MQTT discovery messages from a catalog. Receives the
// catalog object, returns a list of { topic, payload, retain: true }.
import { stateTopic, commandTopic, availabilityTopic } from "./topics.js";

export function buildDiscovery(catalog) {
  const base = catalog.base_topic;
  const messages = [];
  for (const device of catalog.devices ?? []) {
    for (const entity of device.entities ?? []) {
      const payload = {
        name: entity.name,
        unique_id: `${device.id}_${entity.key}`,
        // Stable entity ids, so automations can name them (switch.circuito_maestro_foco).
        default_entity_id: `${entity.component}.${device.id}_${entity.key}`,
        availability_topic: availabilityTopic(base, device.id),
        payload_available: "online",
        payload_not_available: "offline",
        device: {
          identifiers: [device.id],
          name: device.name,
          model: device.model,
          manufacturer: "Project Studio",
          suggested_area: device.area,
        },
      };
      if (entity.component === "switch") {
        payload.command_topic = commandTopic(base, device.id, entity.key);
        payload.state_topic = stateTopic(base, device.id, entity.key);
        payload.payload_on = "ON";
        payload.payload_off = "OFF";
      } else if (entity.component === "button") {
        payload.command_topic = commandTopic(base, device.id, entity.key);
        payload.payload_press = "PRESS";
      } else if (entity.component === "text") {
        payload.command_topic = commandTopic(base, device.id, entity.key);
        payload.state_topic = stateTopic(base, device.id, entity.key);
        payload.max = entity.max ?? 64;
        payload.mode = "text";
      } else if (entity.component === "sensor") {
        payload.state_topic = stateTopic(base, device.id, entity.key);
        if (entity.unit !== undefined) payload.unit_of_measurement = entity.unit;
        if (entity.device_class) payload.device_class = entity.device_class;
      } else if (entity.component === "binary_sensor") {
        payload.state_topic = stateTopic(base, device.id, entity.key);
        payload.payload_on = "ON";
        payload.payload_off = "OFF";
        if (entity.device_class) payload.device_class = entity.device_class;
      } else if (entity.component === "lock") {
        payload.command_topic = commandTopic(base, device.id, entity.key);
        payload.state_topic = stateTopic(base, device.id, entity.key);
        payload.payload_lock = "LOCK";
        payload.payload_unlock = "UNLOCK";
        payload.state_locked = "LOCKED";
        payload.state_unlocked = "UNLOCKED";
      }
      messages.push({
        topic: `homeassistant/${entity.component}/${device.id}/${entity.key}/config`,
        payload,
        retain: true,
      });
    }
  }
  return messages;
}
