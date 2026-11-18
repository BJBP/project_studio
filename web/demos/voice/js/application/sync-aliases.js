// Gives each catalog entity in Home Assistant its short spoken name as an alias, so local voice
// orders ("enciende el foco") find it. Receives { assist (request), catalog }; returns how many it updated.
import { entityAliases } from '../domain/aliases.js';

export async function syncAliases({ assist, catalog }) {
  const wanted = entityAliases(catalog);
  const registry = await assist.request({ type: 'config/entity_registry/list' });
  let updated = 0;
  for (const entry of registry) {
    const aliases = wanted[entry.unique_id];
    if (!aliases || entry.platform !== 'mqtt') continue;
    const current = entry.aliases ?? [];
    const missing = aliases.filter((alias) => !current.includes(alias));
    if (!missing.length) continue;
    await assist.request({ type: 'config/entity_registry/update', entity_id: entry.entity_id, aliases: [...current, ...missing] });
    updated += 1;
  }
  return updated;
}
