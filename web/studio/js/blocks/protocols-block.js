// Protocols block: what Home Assistant can talk to (KNX, Zigbee, Matter, Sonoff…) and the Studio's bridges (Alexa,
// Google). Active ones say so; the others open Home Assistant's own form to add them. List: ../../protocols.json.
import { fill, h } from '../../../shared/dom.js';
import { connectHa } from '../ha-live.js';
import { addLink, protocolRows } from '../protocols.js';

const POLL_MS = 3000;

export function createProtocolsBlock({ t }) {
  const timers = new Set();
  let alive = true, assist = null, catalog = null, haUrl = '', entries = [];
  const bridges = {};
  const list = h('div', { class: 'protocols-list' });
  const status = h('p', { class: 'board-status', role: 'status' });

  const later = (fn, ms) => {
    if (!alive) return;
    const id = setTimeout(() => { timers.delete(id); fn(); }, ms);
    timers.add(id);
  };

  async function bridgeCall(name, on) {
    const response = await fetch('/api/bridge', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, on }),
    });
    bridges[name] = (await response.json()).state;
    draw();
    if (on) later(() => watchBridge(name), POLL_MS);
  }

  async function watchBridge(name) {
    const job = await (await fetch(`/api/bridge/${name}`)).json();
    bridges[name] = job.state;
    if (job.state === 'error') status.textContent = `⚠ ${job.message}`;
    draw();
    if (job.state === 'running') later(() => watchBridge(name), POLL_MS);
  }

  function action(row) {
    if (row.bridge) {
      const page = row.active && row.page ? h('a', { class: 'blocks-button', href: row.page, target: '_blank', rel: 'noopener' }, t('protoPage')) : null;
      return [h('button', { type: 'button', class: 'blocks-button', onclick: () => bridgeCall(row.bridge, !row.active) },
        t(row.active ? 'protoStop' : 'protoStart')), page].filter(Boolean);
    }
    const href = row.active ? `${haUrl}/config/integrations/integration/${encodeURIComponent(row.domain)}` : addLink(haUrl, row.domain);
    return [h('a', { class: 'blocks-button', href, target: '_blank', rel: 'noopener' }, t(row.active ? 'protoOpen' : 'protoAdd'))];
  }

  function draw() {
    if (!catalog) return;
    fill(list, ...protocolRows(catalog, entries, bridges).map((row) => h('div', { class: 'protocol-row', dataset: { active: String(row.active) } },
      h('strong', {}, `${row.icon} ${row.name}`),
      h('span', { class: 'protocol-state' }, t(row.active ? 'protoActive' : 'protoInactive')),
      h('span', { class: 'brain-note' }, row.needs),
      h('span', { class: 'shop-actions' }, ...action(row)))));
  }

  async function load() {
    catalog = await (await fetch('protocols.json')).json();
    haUrl = (await (await fetch('/config.json')).json()).haUrl ?? '';
    for (const p of catalog.protocols.filter((p) => p.bridge)) bridges[p.bridge] = (await (await fetch(`/api/bridge/${p.bridge}`)).json()).state;
    draw();
    assist = await connectHa(t('protoNoHa'));
    entries = await assist.request({ type: 'config_entries/get' });
    draw();
    for (const name of Object.keys(bridges)) if (bridges[name] === 'running') watchBridge(name);
  }

  return {
    id: 'protocols', title: t('blockProtocols'), icon: '🔗', defaultVisible: true, defaultColumn: 'main', optionsSchema: [],
    render(container) {
      fill(container, list, status, h('p', { class: 'board-status' }, t('protoHint')));
      load().catch((error) => { status.textContent = `⚠ ${error.message ?? t('protoNoHa')}`; });
    },
    destroy() {
      alive = false;
      for (const timer of timers) clearTimeout(timer);
      timers.clear();
      assist?.close?.();
    },
  };
}
