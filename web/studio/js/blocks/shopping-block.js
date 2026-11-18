// Shopping block: parts × installations, the brand model for each (from the local data folder), cheapest
// offer, bought ticks and totals per currency. Prices are never invented: missing ones say "a completar".
import { fill, h } from '../../../shared/dom.js';
import { download } from '../api.js';

export function createShoppingBlock({ t, api, projectId }) {
  let list = null;
  let message = '';
  let root = null;
  const base = `projects/${encodeURIComponent(projectId)}/shopping`;

  async function call(path, body) {
    try {
      list = await api(path ? `${base}/${path}` : base, body);
      message = '';
    } catch (error) {
      message = error.message;
    }
    if (root) render(root);
  }

  const modelName = (m) => (m ? `${m.brand} ${m.model}${m.status === 'tested' ? ` ✓ ${t('shopTested')}` : ''}` : t('shopToChoose'));

  function row(item) {
    const bought = h('input', { type: 'checkbox', checked: item.bought, 'aria-label': t('shopBought', { part: item.name }) });
    bought.addEventListener('change', () => call('bought', { part: item.part, bought: bought.checked }));
    const model = item.options.length > 1
      ? h('select', { class: 'talk-input', 'aria-label': t('shopModel'), onchange: (e) => call('model', { part: item.part, model: e.target.value }) },
        item.options.map((m) => h('option', { value: m.id, selected: m.id === item.model?.id }, modelName(m))))
      : modelName(item.model);
    const offer = item.offer;
    return h('tr', {}, h('td', {}, bought), h('td', { title: item.spec }, item.name), h('td', {}, model),
      h('td', { class: 'num' }, item.qty), h('td', {}, offer?.store ?? '—'),
      h('td', { class: 'num' }, offer ? `${offer.price} ${offer.currency}` : t('shopNoPrice')));
  }

  function render(container) {
    if (!list) { fill(container, h('p', {}, message || t('loading'))); return; }
    const units = h('input', { type: 'number', min: 1, max: 999, value: list.units, class: 'talk-input shop-units', id: 'shop-units' });
    units.addEventListener('change', () => call('units', { units: units.value }));
    const totals = Object.entries(list.totals).map(([currency, amount]) => `${amount} ${currency}`).join(' · ') || '—';
    fill(container, 
      h('div', { class: 'shop-head' }, h('label', { for: 'shop-units' }, t('shopUnits')), units),
      h('div', { class: 'studio-table-wrap' }, h('table', { class: 'studio-table' },
        h('thead', {}, h('tr', {}, ['shopColBought', 'shopColPart', 'shopColModel', 'shopColQty', 'shopColStore', 'shopColPrice']
          .map((k) => h('th', { scope: 'col' }, t(k))))),
        h('tbody', {}, list.rows.map(row)))),
      h('p', { class: 'studio-card-meta' }, t('shopSummary', { bought: list.bought, total: list.rows.length, totals }),
        list.missing_prices ? ` · ${t('shopMissing', { n: list.missing_prices })}` : ''),
      list.issues.length ? h('ul', { class: 'slot-issues' }, list.issues.map((i) => h('li', {}, `⚠ ${i.message}`))) : null,
      h('p', { class: 'brain-note' }, t('shopModelsHint')),
      h('div', { class: 'shop-actions' },
        h('button', { type: 'button', class: 'blocks-button', onclick: async () => {
          const docs = await api(`projects/${encodeURIComponent(projectId)}/docs`);
          download('compras.csv', docs['compras.csv'], 'text/csv');
        } }, t('shopCsv')),
        h('button', { type: 'button', class: 'blocks-button', onclick: () => window.print() }, t('shopPrint'))),
      message ? h('p', { class: 'studio-error', role: 'alert' }, message) : null);
  }

  return {
    id: 'shopping', title: t('blockShopping'), icon: '🛒', defaultVisible: true, defaultColumn: 'main', optionsSchema: [],
    render(container) {
      root = container;
      render(container);
      if (!list) call('');
    },
    destroy() { root = null; },
  };
}
