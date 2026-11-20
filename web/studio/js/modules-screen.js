// «Módulos» screen (#/modulos): every module as a tree (submodules under their parent), whether it comes with the
// program or was installed, its license and a switch. A .zip installs or updates a module after showing what it adds;
// installed ones can be uninstalled. A module others need cannot be turned off (the server says why).
import { fill, h } from '../../shared/dom.js';
import { t } from '../../shared/i18n.js';
import { api } from './api.js';
import { moduleTree } from './module-tabs.js';

function adds(module) {
  const tabs = (module.adds?.tabs ?? []).map((tab) => t(`tab.${tab.id}`));
  const blocks = (module.adds?.blocks ?? []).length;
  const connector = module.adds?.connector ? t('moduleAdd.connector', { x: module.name }) : '';
  return [tabs.length ? t('moduleAddsTabs', { tabs: tabs.join(', ') }) : '', blocks ? t('moduleAddsBlocks', { n: blocks }) : '', connector]
    .filter(Boolean).join(' · ');
}

const readBase64 = (file) => new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => resolve(String(reader.result).split(',')[1] ?? '');
  reader.onerror = () => reject({ message: t('issue.E_EXT_BAD_ZIP') });
  reader.readAsDataURL(file);
});

export async function renderModules(view) {
  const list = h('div', { class: 'protocols-list' });
  const status = h('p', { class: 'board-status', role: 'status' });
  const review = h('div', { class: 'connection-form' });
  const picker = h('input', { type: 'file', accept: '.zip,application/zip', hidden: true, onchange: () => inspect() });
  let result = null;

  function row(module, depth) {
    const toggle = h('input', { type: 'checkbox', checked: module.enabled, 'aria-label': module.name,
      onchange: () => change(module.id, toggle.checked) });
    const origin = t(module.origin === 'installed' ? 'modulesInstalled' : 'modulesIncluded');
    return h('div', { class: 'protocol-row', dataset: { active: String(module.active), depth: String(depth) } },
      h('strong', {}, `${depth ? '└ ' : ''}${module.icon ?? '🧩'} ${module.name}`),
      h('label', { class: 'board-check' }, toggle, t(module.enabled ? 'moduleOn' : 'moduleOff')),
      h('span', { class: 'brain-note' }, `${origin} · ${module.description ?? ''} ${module.version} · ${module.license}`),
      h('span', { class: 'brain-note' }, [adds(module), module.requires?.length ? t('moduleRequires', { list: module.requires.join(', ') }) : '']
        .filter(Boolean).join(' · ')),
      module.origin === 'installed'
        ? h('span', { class: 'shop-actions' }, h('button', { type: 'button', class: 'blocks-button', onclick: () => uninstall(module) }, t('modulesUninstall')))
        : null);
  }

  const drawRows = () => fill(list, ...moduleTree(result.modules).map(({ module, depth }) => row(module, depth)));

  function draw(next) {
    result = next;
    drawRows();
    status.textContent = result.issues.map((issue) => `⚠ ${issue.message}`).join(' ');
  }

  async function call(path, body, after) {
    try {
      const reply = await api(path, body);
      after(reply);
    } catch (error) {
      status.textContent = `⚠ ${error.message ?? error.code}`;
    }
  }

  async function change(id, on) {
    await call(`modules/${encodeURIComponent(id)}`, { enabled: on }, draw);
    drawRows();  // after a refusal the switch goes back to the real state; the error stays in the status line
  }

  async function inspect() {
    const file = picker.files?.[0];
    picker.value = '';
    if (!file) return;
    status.textContent = t('modulesReading');
    const zip = await readBase64(file).catch((error) => { status.textContent = `⚠ ${error.message}`; return null; });
    if (zip === null) return;
    await call('modules/inspect', { zip }, (found) => {
      status.textContent = '';
      const parent = result.modules.find((m) => m.id === found.parent);
      const added = found.adds.map((a) => { const [kind, x] = a.split(':'); return t(`moduleAdd.${kind}`, { x: kind === 'connector' ? found.name : x }); });
      fill(review,
        h('h3', {}, `${found.icon ?? '🧩'} ${t('modulesFound', found)}`),
        found.parent ? h('p', { class: 'brain-note' }, t('modulesSubOf', { parent: parent?.name ?? found.parent })) : null,
        found.description ? h('p', { class: 'brain-note' }, found.description) : null,
        added.length ? h('p', { class: 'brain-note' }, t('modulesAdds', { list: added.join(', ') })) : null,
        found.replaces ? h('p', { class: 'brain-note' }, t('modulesReplaces', { version: found.replaces })) : null,
        h('p', { class: 'lic-warn' }, t('modulesTrust')),
        h('div', { class: 'shop-actions' },
          h('button', { type: 'button', class: 'blocks-button', onclick: () => install(zip, found.name) }, t('modulesDoInstall')),
          h('button', { type: 'button', class: 'blocks-button', onclick: () => fill(review) }, t('modulesCancel'))));
    });
  }

  async function install(zip, name) {
    await call('modules/install', { zip }, (next) => { fill(review); draw(next); status.textContent = t('modulesInstalledOk', { name }); });
  }

  async function uninstall(module) {
    if (!confirm(t('modulesConfirmUninstall', { name: module.name }))) return;
    await call(`modules/${encodeURIComponent(module.id)}/uninstall`, {}, (next) => { draw(next); status.textContent = t('modulesUninstalledOk'); });
  }

  view.append(h('div', { class: 'studio-heading' }, h('h1', {}, t('modulesTitle')),
    h('button', { type: 'button', class: 'blocks-button', onclick: () => picker.click() }, t('modulesInstall'))),
  h('p', { class: 'brain-note' }, t('modulesHint')), picker, review, list, status);
  draw(await api('modules'));
  return null;
}
