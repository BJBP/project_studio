import test from 'node:test';
import assert from 'node:assert/strict';

import {
  defaultLayout,
  hideBlock,
  mergeWithDefaults,
  moveBlock,
  setOption,
  showBlock,
} from '../../web/engines/blocks/layout.js';

const columns = [
  { id: 'main', title: 'Principal' },
  { id: 'side', title: 'Lateral' },
];

const blocks = [
  {
    id: 'alpha',
    title: 'Alpha',
    icon: 'A',
    defaultVisible: true,
    defaultColumn: 'main',
    optionsSchema: [
      { key: 'enabled', label: 'Enabled', type: 'boolean', default: true },
      { key: 'step', label: 'Step', type: 'number', default: 1, min: 1, max: 10 },
      { key: 'mode', label: 'Mode', type: 'select', default: 'a', choices: ['a', 'b'] },
      { key: 'name', label: 'Name', type: 'text', default: 'x' },
    ],
  },
  {
    id: 'beta',
    title: 'Beta',
    icon: 'B',
    defaultVisible: true,
    defaultColumn: 'main',
    optionsSchema: [],
  },
  {
    id: 'gamma',
    title: 'Gamma',
    icon: 'C',
    defaultVisible: true,
    defaultColumn: 'side',
    optionsSchema: [],
  },
  {
    id: 'secret',
    title: 'Secret',
    icon: 'D',
    defaultVisible: false,
    defaultColumn: 'main',
    optionsSchema: [],
  },
];

test('defaultLayout places visible blocks in their columns and hidden ones in hidden', () => {
  const layout = defaultLayout(blocks, columns);
  assert.equal(layout.version, 1);
  assert.deepEqual(layout.columns.find((c) => c.id === 'main').blocks, ['alpha', 'beta']);
  assert.deepEqual(layout.columns.find((c) => c.id === 'side').blocks, ['gamma']);
  assert.deepEqual(layout.hidden, ['secret']);
  assert.deepEqual(layout.options.alpha, { enabled: true, step: 1, mode: 'a', name: 'x' });
});

test('defaultLayout does not mutate its inputs and returns fresh objects', () => {
  const layout = defaultLayout(blocks, columns);
  layout.columns[0].blocks.push('mutated');
  const fresh = defaultLayout(blocks, columns);
  assert.deepEqual(fresh.columns[0].blocks, ['alpha', 'beta']);
});

test('moveBlock moves a block between columns and clamps the index', () => {
  const layout = defaultLayout(blocks, columns);
  const moved = moveBlock(layout, 'alpha', 'side', 99);
  assert.deepEqual(moved.columns.find((c) => c.id === 'main').blocks, ['beta']);
  assert.deepEqual(moved.columns.find((c) => c.id === 'side').blocks, ['gamma', 'alpha']);
  // Original layout is untouched.
  assert.deepEqual(layout.columns.find((c) => c.id === 'main').blocks, ['alpha', 'beta']);
});

test('moveBlock reorders within the same column', () => {
  const layout = defaultLayout(blocks, columns);
  const moved = moveBlock(layout, 'beta', 'main', 0);
  assert.deepEqual(moved.columns.find((c) => c.id === 'main').blocks, ['beta', 'alpha']);
});

test('hideBlock removes the block from its column and lists it as hidden', () => {
  const layout = defaultLayout(blocks, columns);
  const hidden = hideBlock(layout, 'alpha');
  assert.deepEqual(hidden.columns.find((c) => c.id === 'main').blocks, ['beta']);
  assert.deepEqual(hidden.hidden, ['secret', 'alpha']);
});

test('showBlock returns a hidden block to the requested column', () => {
  const layout = defaultLayout(blocks, columns);
  const shown = showBlock(layout, 'secret', 'side');
  assert.deepEqual(shown.hidden, []);
  assert.deepEqual(shown.columns.find((c) => c.id === 'side').blocks, ['gamma', 'secret']);
});

test('setOption accepts a valid value and returns a new layout', () => {
  const layout = defaultLayout(blocks, columns);
  const updated = setOption(layout, blocks[0].optionsSchema, 'alpha', 'step', 5);
  assert.equal(updated.options.alpha.step, 5);
  assert.equal(layout.options.alpha.step, 1);
});

test('setOption rejects out-of-range, wrong-type and unknown values', () => {
  const layout = defaultLayout(blocks, columns);
  const schema = blocks[0].optionsSchema;
  assert.deepEqual(setOption(layout, schema, 'alpha', 'step', 11), { error: 'E_OPTION_INVALID' });
  assert.deepEqual(setOption(layout, schema, 'alpha', 'step', 0), { error: 'E_OPTION_INVALID' });
  assert.deepEqual(setOption(layout, schema, 'alpha', 'step', '3'), { error: 'E_OPTION_INVALID' });
  assert.deepEqual(setOption(layout, schema, 'alpha', 'enabled', 'yes'), { error: 'E_OPTION_INVALID' });
  assert.deepEqual(setOption(layout, schema, 'alpha', 'mode', 'z'), { error: 'E_OPTION_INVALID' });
  assert.deepEqual(setOption(layout, schema, 'alpha', 'unknown', 1), { error: 'E_OPTION_INVALID' });
});

test('mergeWithDefaults adds new blocks according to their defaults', () => {
  const layout = defaultLayout(blocks, columns);
  const saved = {
    ...layout,
    columns: layout.columns.map((column) => ({ ...column, blocks: [...column.blocks] })),
    hidden: [...layout.hidden],
    options: JSON.parse(JSON.stringify(layout.options)),
  };
  const blocksWithNew = [
    ...blocks,
    {
      id: 'delta',
      title: 'Delta',
      icon: 'E',
      defaultVisible: true,
      defaultColumn: 'side',
      optionsSchema: [{ key: 'level', label: 'Level', type: 'number', default: 3, min: 1, max: 5 }],
    },
    {
      id: 'epsilon',
      title: 'Epsilon',
      icon: 'F',
      defaultVisible: false,
      defaultColumn: 'main',
      optionsSchema: [],
    },
  ];
  const merged = mergeWithDefaults(saved, blocksWithNew, columns);
  assert.deepEqual(merged.columns.find((c) => c.id === 'side').blocks, ['gamma', 'delta']);
  assert.deepEqual(merged.hidden, ['secret', 'epsilon']);
  assert.equal(merged.options.delta.level, 3);
});

test('mergeWithDefaults removes blocks that no longer exist', () => {
  const layout = defaultLayout(blocks, columns);
  const merged = mergeWithDefaults(layout, blocks.filter((block) => block.id !== 'beta'), columns);
  assert.deepEqual(merged.columns.find((c) => c.id === 'main').blocks, ['alpha']);
  assert.equal(merged.options.beta, undefined);
});

test('mergeWithDefaults drops saved option values that are now invalid', () => {
  const layout = defaultLayout(blocks, columns);
  layout.options.alpha.step = 500;
  const merged = mergeWithDefaults(layout, blocks, columns);
  assert.equal(merged.options.alpha.step, 1);
});

test('mergeWithDefaults with a different version returns the default layout', () => {
  const layout = defaultLayout(blocks, columns);
  const merged = mergeWithDefaults({ ...layout, version: 99 }, blocks, columns);
  assert.deepEqual(merged, defaultLayout(blocks, columns));
});
