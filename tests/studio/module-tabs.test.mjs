// Project tabs from the active modules: order, "when", blocks from other modules, and turned-off modules.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { moduleTree, tabsFromModules } from '../../web/studio/js/module-tabs.js';

const block = (tab, name) => ({ tab, entry: `js/blocks/${name}.js`, export: name });
const result = {
  active: ['devices', 'protocols', 'flow'],
  modules: [
    { id: 'flow', adds: { tabs: [{ id: 'flow', order: 20 }], blocks: [block('flow', 'flowBlock')] } },
    { id: 'devices', adds: { tabs: [{ id: 'devices', order: 60, when: 'project.devices' }], blocks: [block('devices', 'twin')] } },
    { id: 'protocols', adds: { blocks: [block('devices', 'protocols')] } },
    { id: 'demo', adds: { tabs: [{ id: 'demo', order: 80 }], blocks: [block('demo', 'demo')] } },
  ],
};

test('active modules give their tabs in order, with blocks added by other modules', () => {
  const tabs = tabsFromModules(result, { project: { devices: [{ id: 'board' }] } });
  assert.deepEqual(tabs.map((t) => t.id), ['flow', 'devices']);
  assert.deepEqual(tabs[1].blocks.map((b) => b.export), ['twin', 'protocols']);
});

test('a tab whose "when" is empty in the project is left out', () => {
  assert.deepEqual(tabsFromModules(result, { project: { devices: [] } }).map((t) => t.id), ['flow']);
});

test('the module tree puts submodules under their parent; an orphan stays at the top', () => {
  const modules = [{ id: 'b', order: 2 }, { id: 'sub', parent: 'a' }, { id: 'a', order: 1 }, { id: 'orphan', parent: 'gone' }];
  assert.deepEqual(moduleTree(modules).map(({ module, depth }) => `${depth}${module.id}`), ['0a', '1sub', '0b', '0orphan']);
});
