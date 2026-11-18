// Pure layout state helpers for the blocks engine.
// Receives plain data (blocks, columns, layout) and returns new layouts.
// No DOM access here; safe to run in Node and the browser.

export const LAYOUT_VERSION = 1;

export function defaultLayout(blocks, columns) {
  const layout = {
    version: LAYOUT_VERSION,
    columns: columns.map((column) => ({ id: column.id, blocks: [] })),
    hidden: [],
    options: {},
  };
  for (const block of blocks) {
    layout.options[block.id] = schemaDefaults(block);
    if (block.defaultVisible === false) {
      layout.hidden.push(block.id);
      continue;
    }
    targetColumn(layout, block.defaultColumn).blocks.push(block.id);
  }
  return layout;
}

export function moveBlock(layout, blockId, toColumnId, toIndex) {
  const next = clone(layout);
  const target = next.columns.find((column) => column.id === toColumnId);
  if (!target) return next;
  if (!removeEverywhere(next, blockId)) return next;
  const index = clampIndex(toIndex, target.blocks.length);
  target.blocks.splice(index, 0, blockId);
  return next;
}

export function hideBlock(layout, blockId) {
  const next = clone(layout);
  if (!removeEverywhere(next, blockId)) return next;
  if (!next.hidden.includes(blockId)) next.hidden.push(blockId);
  return next;
}

export function showBlock(layout, blockId, columnId) {
  const next = clone(layout);
  if (!next.columns.length) {
    if (!next.hidden.includes(blockId)) next.hidden.push(blockId);
    return next;
  }
  if (!removeEverywhere(next, blockId)) return next;
  targetColumn(next, columnId).blocks.push(blockId);
  return next;
}

export function setOption(layout, schema, blockId, key, value) {
  const field = (schema ?? []).find((entry) => entry.key === key);
  if (!field || !isValueValid(field, value)) return { error: 'E_OPTION_INVALID' };
  const next = clone(layout);
  next.options = next.options ?? {};
  next.options[blockId] = { ...(next.options[blockId] ?? {}), [key]: value };
  return next;
}

export function mergeWithDefaults(saved, blocks, columns) {
  if (!saved || saved.version !== LAYOUT_VERSION) return defaultLayout(blocks, columns);

  const blockById = new Map(blocks.map((block) => [block.id, block]));
  const knownColumnIds = new Set(columns.map((column) => column.id));
  const placed = new Set();
  const next = {
    version: LAYOUT_VERSION,
    columns: columns.map((column) => ({ id: column.id, blocks: [] })),
    hidden: [],
    options: {},
  };
  const firstColumn = next.columns[0];

  const take = (ids) => {
    const result = [];
    for (const id of ids ?? []) {
      if (!blockById.has(id) || placed.has(id)) continue;
      placed.add(id);
      result.push(id);
    }
    return result;
  };

  // Keep the saved order inside known columns; unknown columns fall back to the first one.
  for (const savedColumn of saved.columns ?? []) {
    const ids = take(savedColumn.blocks);
    if (!ids.length) continue;
    const target = knownColumnIds.has(savedColumn.id)
      ? next.columns.find((column) => column.id === savedColumn.id)
      : firstColumn;
    target.blocks.push(...ids);
  }

  next.hidden = take(saved.hidden);

  // New blocks are added according to their defaults.
  for (const block of blocks) {
    if (placed.has(block.id)) continue;
    placed.add(block.id);
    if (block.defaultVisible === false) {
      next.hidden.push(block.id);
    } else {
      targetColumn(next, block.defaultColumn).blocks.push(block.id);
    }
  }

  // Options: defaults, overridden by saved values that still validate.
  for (const block of blocks) {
    const options = schemaDefaults(block);
    const savedOptions = saved.options?.[block.id] ?? {};
    for (const field of block.optionsSchema ?? []) {
      if (Object.prototype.hasOwnProperty.call(savedOptions, field.key)
        && isValueValid(field, savedOptions[field.key])) {
        options[field.key] = savedOptions[field.key];
      }
    }
    next.options[block.id] = options;
  }

  return next;
}

function schemaDefaults(block) {
  const defaults = {};
  for (const field of block.optionsSchema ?? []) defaults[field.key] = field.default;
  return defaults;
}

function targetColumn(layout, columnId) {
  return layout.columns.find((column) => column.id === columnId) ?? layout.columns[0];
}

function removeEverywhere(layout, blockId) {
  let found = false;
  for (const column of layout.columns) {
    const before = column.blocks.length;
    column.blocks = column.blocks.filter((id) => id !== blockId);
    if (column.blocks.length !== before) found = true;
  }
  if (layout.hidden.includes(blockId)) {
    layout.hidden = layout.hidden.filter((id) => id !== blockId);
    found = true;
  }
  return found;
}

function clampIndex(index, length) {
  if (typeof index !== 'number' || Number.isNaN(index)) return length;
  return Math.max(0, Math.min(Math.trunc(index), length));
}

function choiceValue(choice) {
  return choice !== null && typeof choice === 'object' ? choice.value : choice;
}

function isValueValid(field, value) {
  switch (field.type) {
    case 'boolean':
      return typeof value === 'boolean';
    case 'number':
      return typeof value === 'number' && Number.isFinite(value)
        && (field.min === undefined || value >= field.min)
        && (field.max === undefined || value <= field.max);
    case 'select':
      return (field.choices ?? []).some((choice) => choiceValue(choice) === value);
    case 'text':
      return typeof value === 'string';
    default:
      return false;
  }
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}
