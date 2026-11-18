// Licenses block (table of each software piece: license, commercial use, notes, alerts) and Documents block
// (downloads licencias.md, THIRD_PARTY_NOTICES.md and compras.csv for the client).
import { fill, h } from '../../../shared/dom.js';
import { download } from '../api.js';

const COMMERCIAL = { yes: 'commercialYes', conditions: 'commercialConditions', no: 'commercialNo' };
const LEVEL = { yes: 'ok', conditions: 'warn', no: 'error' };

export function createLicensesBlock({ t, store }) {
  let unsubscribe = null;

  function render(container) {
    const { rows, alerts, level } = store.view.licenses;
    fill(container, 
      h('p', { class: `slot-license lic-${level}` }, t(`licensesLevel.${level}`)),
      h('div', { class: 'studio-table-wrap' }, h('table', { class: 'studio-table' },
        h('thead', {}, h('tr', {}, ['licColPiece', 'licColLicense', 'licColCommercial', 'licColNotes'].map((k) => h('th', { scope: 'col' }, t(k))))),
        h('tbody', {}, rows.map((r) => h('tr', {},
          h('td', {}, r.name), h('td', {}, r.spdx),
          h('td', { class: `lic-${LEVEL[r.commercial]}` }, t(COMMERCIAL[r.commercial])), h('td', {}, r.notes)))))),
      alerts.length ? h('ul', { class: 'slot-issues' }, alerts.map((a) => h('li', {}, `⚠ ${a.message}`))) : null,
      h('p', { class: 'brain-note' }, t('licensesDisclaimer')));
  }

  return {
    id: 'licenses', title: t('blockLicenses'), icon: '⚖️', defaultVisible: true, defaultColumn: 'main', optionsSchema: [],
    render(container) {
      render(container);
      unsubscribe?.();
      unsubscribe = store.subscribe(() => render(container));
    },
    destroy() { unsubscribe?.(); unsubscribe = null; },
  };
}

export function createDocsBlock({ t, api, projectId }) {
  const FILES = [['licencias.md', 'text/markdown'], ['THIRD_PARTY_NOTICES.md', 'text/markdown'], ['compras.csv', 'text/csv'],
    ['inventree_partes.csv', 'text/csv'], ['odoo_productos.csv', 'text/csv']];
  return {
    id: 'docs', title: t('blockDocs'), icon: '📄', defaultVisible: true, defaultColumn: 'side', optionsSchema: [],
    render(container) {
      const message = h('p', { class: 'studio-error', role: 'alert', hidden: true });
      const get = async (name, type) => {
        try {
          const docs = await api(`projects/${encodeURIComponent(projectId)}/docs`);
          download(name, docs[name], type);
        } catch (error) {
          message.textContent = error.message;
          message.hidden = false;
        }
      };
      fill(container, h('p', { class: 'brain-note' }, t('docsIntro')),
        h('div', { class: 'shop-actions' }, FILES.map(([name, type]) =>
          h('button', { type: 'button', class: 'blocks-button', onclick: () => get(name, type) }, `⬇ ${name}`))), message);
    },
  };
}
