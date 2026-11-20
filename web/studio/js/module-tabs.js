// The project's tabs, built from the active modules (GET /api/studio/modules), and the module tree; pure: no DOM.
// moduleTree(modules) -> [{ module, depth }]: each module followed by its submodules ("parent"), in order.
// tabsFromModules(result, view) -> [{ id, order, blocks: [{ entry, export }] }]: only active modules, tabs whose
// "when" (a path in the project view, e.g. "project.devices") has something, and tabs with at least one block.

const has = (view, path) => {
  const value = path.split('.').reduce((obj, key) => obj?.[key], view);
  return Array.isArray(value) ? value.length > 0 : Boolean(value);
};

export function tabsFromModules(result, view) {
  const active = result.modules.filter((m) => result.active.includes(m.id));
  const tabs = new Map();
  for (const module of active) {
    for (const tab of module.adds?.tabs ?? []) {
      if (!tab.when || has(view, tab.when)) tabs.set(tab.id, { id: tab.id, order: tab.order ?? 99, blocks: [] });
    }
  }
  for (const module of active) {
    for (const block of module.adds?.blocks ?? []) tabs.get(block.tab)?.blocks.push({ entry: block.entry, export: block.export });
  }
  return [...tabs.values()].filter((tab) => tab.blocks.length).sort((a, b) => a.order - b.order);
}

export function moduleTree(modules) {
  const ids = new Set(modules.map((m) => m.id));
  const byOrder = (a, b) => (a.order ?? 99) - (b.order ?? 99) || a.id.localeCompare(b.id);
  const childrenOf = (id) => modules.filter((m) => m.parent === id).sort(byOrder);
  const walk = (module, depth, seen) => (seen.has(module.id) ? [] : [{ module, depth },
    ...childrenOf(module.id).flatMap((child) => walk(child, depth + 1, new Set([...seen, module.id])))]);
  return modules.filter((m) => !m.parent || !ids.has(m.parent)).sort(byOrder).flatMap((m) => walk(m, 0, new Set()));
}
