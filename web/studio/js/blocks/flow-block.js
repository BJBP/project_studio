// Flow block: the install stages (Comprar → … → Soporte) with their checklists and the overall progress.
// Ticking saves at once; items can open the 3D tutorial, the demo or download the delivery documents.
import { fill, h } from '../../../shared/dom.js';
import { download } from '../api.js';

export function createFlowBlock({ t, api, store, projectId }) {
  let unsubscribe = null;
  let open = null; // stage id shown; null = first stage not finished
  let message = '';
  const base = `projects/${encodeURIComponent(projectId)}`;

  async function tick(item, done) {
    try {
      store.view.flow = await api(`${base}/flow`, { item, done });
      message = '';
    } catch (error) {
      message = error.message;
    }
    store.emit();
  }

  async function itemAction(item) {
    if (item.link === 'demo') location.hash = `#/p/${encodeURIComponent(projectId)}/demo`;
    else if (item.link) window.open(store.view.project.links?.[item.link], '_blank', 'noopener');
    else if (item.download === 'licenses') {
      const docs = await api(`${base}/docs`);
      for (const name of ['licencias.md', 'THIRD_PARTY_NOTICES.md']) download(name, docs[name], 'text/markdown');
    }
  }

  function itemRow(item) {
    const box = h('input', { type: 'checkbox', id: `flow-${item.id}`, checked: item.done });
    box.addEventListener('change', () => tick(item.id, box.checked));
    const action = item.link || item.download
      ? h('button', { type: 'button', class: 'blocks-button flow-open', onclick: () => itemAction(item) }, t(`flowAction.${item.link ?? item.download}`))
      : null;
    return h('li', { class: 'flow-item' }, box, h('label', { for: `flow-${item.id}` }, item.text), action);
  }

  function render(container) {
    const flow = store.view.flow;
    const current = open ?? (flow.stages.find((s) => s.done < s.total) ?? flow.stages[0]).id;
    const stage = flow.stages.find((s) => s.id === current);
    const chips = h('div', { class: 'flow-stages', role: 'tablist', 'aria-label': t('flowStages') },
      flow.stages.map((s, index) => h('button', {
        type: 'button', role: 'tab', class: 'flow-stage', 'aria-selected': String(s.id === current),
        dataset: { state: s.done === s.total ? 'done' : s.done ? 'partial' : 'todo' },
        onclick: () => { open = s.id; render(container); },
      }, `${index ? '► ' : ''}${s.name} ${s.done}/${s.total}`)));
    const percent = flow.total ? Math.round((100 * flow.done) / flow.total) : 0;
    fill(container, chips,
      h('ul', { class: 'flow-items' }, stage.items.length ? stage.items.map(itemRow) : h('li', {}, t('flowEmpty'))),
      h('p', { class: 'studio-card-meta' }, t('cardProgress', { done: flow.done, total: flow.total })),
      h('span', { class: 'studio-progress', role: 'progressbar', 'aria-valuenow': percent, 'aria-valuemin': 0,
        'aria-valuemax': 100, 'aria-label': t('flowProgress') }, h('span', { style: `width:${percent}%` })),
      message ? h('p', { class: 'studio-error', role: 'alert' }, message) : null);
  }

  return {
    id: 'flow', title: t('blockFlow'), icon: '🗂️', defaultVisible: true, defaultColumn: 'main', optionsSchema: [],
    render(container) {
      render(container);
      unsubscribe?.();
      unsubscribe = store.subscribe(() => render(container));
    },
    destroy() { unsubscribe?.(); unsubscribe = null; },
  };
}
