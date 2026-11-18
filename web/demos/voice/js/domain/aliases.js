// Spoken names for each catalog entity. Receives the catalog, returns { uniqueId: [alias] }.
// HA names MQTT entities "<device> <entity>" ("Circuito maestro Foco"); the alias lets people say just "foco".
export function entityAliases(catalog) {
  const aliases = {};
  for (const device of catalog.devices ?? []) {
    for (const entity of device.entities ?? []) aliases[`${device.id}_${entity.key}`] = [entity.name];
  }
  return aliases;
}
