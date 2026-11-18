// Slot block: the piece chosen for the selected slot, its alternatives, license and what breaks when it changes.
// "Restablecer" brings back the original piece.
import { fill, h } from '../../../shared/dom.js';

const COMMERCIAL = { yes: 'commercialYes', conditions: 'commercialConditions', no: 'commercialNo' };

export function createSlotBlock({ t, api, store, projectId }) {
  let unsubscribe = null;
  let message = '';

  async function change(path, body) {
    try {
      message = '';
      store.apply(await api(`projects/${encodeURIComponent(projectId)}/${path}`, body));
    } catch (error) {
      message = error.message;
      store.emit();
    }
  }

  function render(container) {
    const slot = store.selected;
    const choice = store.view.project.slots[slot];
    if (!choice) { fill(container, h('p', { class: 'studio-empty' }, t('slotNone'))); return; }
    const info = choice.info ?? {};
    const select = h('select', { class: 'talk-input', id: 'slot-select', 'aria-label': t('slotPiece') },
      choice.alternatives.map((alt) => h('option', { value: alt.id, selected: alt.id === choice.component }, alt.name)));
    select.addEventListener('change', () => change('swap', { slot, component: select.value }));
    const issues = store.view.issues.filter((i) => i.slot === slot);
    const lic = info.license;
    fill(container, 
      h('p', { class: 'slot-title' }, t('slotTitle', { slot: t(`slot.${slot}`) })),
      h('label', { for: 'slot-select', class: 'talk-input-label' }, t('slotPiece')), select,
      lic ? h('p', { class: `slot-license lic-${lic.commercial === 'yes' ? 'ok' : lic.commercial === 'no' ? 'error' : 'warn'}` },
        `${lic.spdx} · ${t(COMMERCIAL[lic.commercial])}`) : h('p', { class: 'slot-license' }, info.spec ?? ''),
      lic?.notes ? h('p', { class: 'brain-note' }, lic.notes) : null,
      issues.length ? h('ul', { class: 'slot-issues', role: 'alert' }, issues.map((i) => h('li', {}, `⚠ ${i.message}`)))
        : h('p', { class: 'lic-ok' }, t('slotCompatible')),
      choice.default && choice.default !== choice.component
        ? h('button', { type: 'button', class: 'blocks-button', onclick: () => change('reset', { slot }) }, t('slotReset')) : null,
      info.docs ? h('a', { href: info.docs, target: '_blank', rel: 'noopener noreferrer', class: 'brain-key-help' }, t('slotDocs')) : null,
      message ? h('p', { class: 'studio-error', role: 'alert' }, message) : null,
      store.view.issues.length ? h('p', { class: 'lic-error' }, t('projectProblems', { n: store.view.issues.length })) : null);
  }

  return {
    id: 'slot',
    title: t('blockSlot'),
    icon: '🔧',
    defaultVisible: true,
    defaultColumn: 'side',
    optionsSchema: [],
    render(container) {
      render(container);
      unsubscribe?.();
      unsubscribe = store.subscribe(() => render(container));
    },
    destroy() { unsubscribe?.(); unsubscribe = null; },
  };
}
