// Builds MQTT topic names for the voice demo. Receives the base topic and
// device/entity identifiers, returns the topic string.
export function stateTopic(base, deviceId, key) {
  return `${base}/${deviceId}/${key}/state`;
}

export function commandTopic(base, deviceId, key) {
  return `${base}/${deviceId}/${key}/set`;
}

export function availabilityTopic(base, deviceId) {
  return `${base}/${deviceId}/status`;
}
