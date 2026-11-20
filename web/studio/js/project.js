// Project screen: one tab per active module (modules/<id>/module.json: Arquitectura, Flujo, Compras…). Each tab is a board of
// movable blocks; all blocks share one store with the project view from the API.
import { h } from '../../shared/dom.js';
import { t, localeTable } from '../../shared/i18n.js';
import { mountBlocks } from '../../engines/blocks/block-manager.js';
import { createStorage } from '../../engines/blocks/storage.js';
import { api } from './api.js';
import { tabsFromModules } from './module-tabs.js';

function createStore(projectId, view) {
  const listeners = new Set();
  const store = {
    projectId, view, selected: Object.keys(view.project.slots)[0],
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    emit() { for (const fn of [...listeners]) fn(); },
    apply(next) { store.view = next; store.emit(); },
    async reload() { store.apply(await api(`projects/${encodeURIComponent(projectId)}`)); },
    select(slot) { if (store.view.project.slots[slot]) { store.selected = slot; store.emit(); } },
  };
  return store;
}

function tabBar(projectId, tabs, active) {
  return h('nav', { class: 'studio-tabs', role: 'tablist', 'aria-label': t('tabsLabel') },
    tabs.map((tab) => h('a', {
      role: 'tab', class: 'studio-tab', href: `#/p/${encodeURIComponent(projectId)}/${tab.id}`,
      'aria-selected': String(tab.id === active.id), dataset: { tab: tab.id },
    }, t(`tab.${tab.id}`))));
}

export async function renderProject(view, projectId, tabId) {
  const data = await api(`projects/${encodeURIComponent(projectId)}`);
  const store = createStore(projectId, data);
  const tabs = tabsFromModules(await api('modules'), data);
  const active = tabs.find((tab) => tab.id === tabId) ?? tabs[0];
  if (!active) throw { code: 'E_NO_MODULES', message: t('noModules') };
  // Each block is loaded when its tab opens: a module's files are only fetched when it is shown.
  const factories = await Promise.all(active.blocks.map(async (b) => (await import(`/studio/${b.entry}`))[b.export]));
  const board = h('div', { class: 'studio-board' });
  const project = data.project;
  view.append(
    h('div', { class: 'studio-heading' },
      h('h1', {}, `${project.icon} ${project.name}`),
      h('span', { class: `studio-badge status-${project.status}` }, t(`status.${project.status}`))),
    tabBar(projectId, tabs, active), board);

  const ctx = { t, api, store, projectId };
  const blocks = factories.map((create) => create(ctx));
  // A tab whose blocks all live in the main column gets no empty side column.
  const columns = [{ id: 'main', title: t('columnMain') }];
  if (blocks.some((block) => block.defaultColumn === 'side')) columns.push({ id: 'side', title: t('columnSide') });
  board.dataset.columns = String(columns.length);
  const mounted = mountBlocks(board, {
    blocks,
    columns,
    storage: createStorage(`studio.tab.${active.id}.layout`),
    t: localeTable,
  });
  // The guided tours change pieces and select them; the screen follows.
  const onRefresh = () => store.reload().catch((error) => console.warn('studio: no se pudo recargar', error));
  const onSelect = (event) => store.select(event.detail);
  window.addEventListener('studio:refresh', onRefresh);
  window.addEventListener('studio:select', onSelect);
  return {
    destroy() {
      window.removeEventListener('studio:refresh', onRefresh);
      window.removeEventListener('studio:select', onSelect);
      mounted.destroy();
    },
  };
}
