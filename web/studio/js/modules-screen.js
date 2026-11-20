// «Módulos» screen (#/modulos): every module the program brings, what it adds and its license, with a switch to turn
// it on or off. A module others need cannot be turned off (the server says why). renderModules(view) -> null.
import { fill, h } from '../../shared/dom.js';
import { t } from '../../shared/i18n.js';
import { api } from './api.js';

function adds(module) {
  const tabs = (module.adds?.tabs ?? []).map((tab) => t(`tab.${tab.id}`));
  const blocks = (module.adds?.blocks ?? []).length;
  return [tabs.length ? t('moduleAddsTabs', { tabs: tabs.join(', ') }) : '', blocks ? t('moduleAddsBlocks', { n: blocks }) : '']
    .filter(Boolean).join(' · ');
}

export async function renderModules(view) {
  const list = h('div', { class: 'protocols-list' });
  const status = h('p', { class: 'board-status', role: 'status' });

  function draw(result) {
    fill(list, ...result.modules.map((module) => {
      const toggle = h('input', { type: 'checkbox', checked: module.enabled, 'aria-label': module.name,
        onchange: () => change(module.id, toggle.checked, toggle) });
      return h('div', { class: 'protocol-row', dataset: { active: String(module.active) } },
        h('strong', {}, `${module.icon ?? '🧩'} ${module.name}`),
        h('label', { class: 'board-check' }, toggle, t(module.enabled ? 'moduleOn' : 'moduleOff')),
        h('span', { class: 'brain-note' }, `${module.description ?? ''} ${module.version} · ${module.license}`),
        h('span', { class: 'brain-note' }, [adds(module), module.requires?.length ? t('moduleRequires', { list: module.requires.join(', ') }) : '']
          .filter(Boolean).join(' · ')));
    }));
    status.textContent = result.issues.map((issue) => `⚠ ${issue.message}`).join(' ');
  }

  async function change(id, on, toggle) {
    try {
      draw(await api(`modules/${encodeURIComponent(id)}`, { enabled: on }));
    } catch (error) {
      toggle.checked = !on;
      status.textContent = `⚠ ${error.message ?? error}`;
    }
  }

  view.append(h('div', { class: 'studio-heading' }, h('h1', {}, t('modulesTitle'))),
    h('p', { class: 'brain-note' }, t('modulesHint')), list, status);
  draw(await api('modules'));
  return null;
}
