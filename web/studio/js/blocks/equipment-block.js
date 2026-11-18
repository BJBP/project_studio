// Equipment block: each computer of the project (laptop for the demo, client mini PC as a profile), whether the
// project fits, which variant each AI piece uses there and its expected answer time.
import { fill, h } from '../../../shared/dom.js';

export function createEquipmentBlock({ t, store }) {
  let unsubscribe = null;

  const card = (eq) => h('section', { class: 'equipment-card', dataset: { ok: String(eq.ok) } },
    h('h3', {}, `${eq.icon} ${eq.name}`),
    h('p', { class: 'brain-note' }, eq.role),
    h('p', { class: eq.ok ? 'lic-ok' : 'lic-error' },
      t('eqMemory', { need: eq.ram_needed, have: eq.ram_total }), ' · ', t(eq.gpu ? 'eqGpu' : 'eqNoGpu')),
    h('ul', { class: 'equipment-items' }, eq.items.filter((i) => i.variant || i.speed).map((i) =>
      h('li', {}, `${i.component}: ${i.variant ?? ''}${i.speed ? ` (${i.speed})` : ''}`))),
    eq.issues.length ? h('ul', { class: 'slot-issues' }, eq.issues.map((i) => h('li', {}, `⚠ ${i.message}`))) : null);

  function render(container) {
    const list = store.view.equipment;
    fill(container, list.length
      ? h('div', { class: 'equipment-list' }, list.map(card), h('p', { class: 'brain-note' }, t('eqHint')))
      : h('p', { class: 'studio-empty' }, t('eqNone')));
  }

  return {
    id: 'equipment', title: t('blockEquipment'), icon: '🖥️', defaultVisible: true, defaultColumn: 'main', optionsSchema: [],
    render(container) {
      render(container);
      unsubscribe?.();
      unsubscribe = store.subscribe(() => render(container));
    },
    destroy() { unsubscribe?.(); unsubscribe = null; },
  };
}
