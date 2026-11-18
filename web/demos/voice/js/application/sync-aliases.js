// Tidies the catalog entities in Home Assistant: each gets its short spoken name as an alias ("foco") and a
// stable id (switch.circuito_maestro_foco) that automations can name. Receives { assist (request), catalog };
// returns how many it updated. One entity that fails does not stop the rest.
import { entityAliases } from '../domain/aliases.js';

function changesFor(entry, wanted) {
  const aliases = wanted[entry.unique_id];
  if (!aliases || entry.platform !== 'mqtt') return null;
  const current = entry.aliases ?? [];
  const missing = aliases.filter((alias) => !current.includes(alias));
  const stableId = `${entry.entity_id.split('.')[0]}.${entry.unique_id}`;
  const update = {};
  if (missing.length) update.aliases = [...current, ...missing];
  if (entry.entity_id !== stableId) update.new_entity_id = stableId;
  return Object.keys(update).length ? update : null;
}

export async function syncAliases({ assist, catalog }) {
  const wanted = entityAliases(catalog);
  const registry = await assist.request({ type: 'config/entity_registry/list' });
  let updated = 0;
  for (const entry of registry) {
    const update = changesFor(entry, wanted);
    if (!update) continue;
    try {
      await assist.request({ type: 'config/entity_registry/update', entity_id: entry.entity_id, ...update });
      updated += 1;
    } catch (error) {
      console.warn(`sync-aliases: no se pudo ordenar ${entry.entity_id}`, error);
    }
  }
  return updated;
}
