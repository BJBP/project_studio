// External connections block: the platforms Home Assistant's devices are shared with, their live state, and a form to
// add or change one (options from its connector's schema, the devices it shares and whether it may give them orders).
// Data: /api/studio/connections (connections.json in the data folder); devices: Home Assistant's states.
import { fill, h } from '../../../shared/dom.js';
import { api } from '../api.js';
import { connectHa } from '../ha-live.js';
import { agoParts, draft, share, shareable, summary, uniqueId } from '../connections.js';

const POLL_MS = 5000;
const MAX_LISTED = 40;
const MARK = { ok: '✓', error: '⚠', paused: '⏸', waiting: '…' };

export function createConnectionsBlock({ t }) {
  let alive = true, timer = null, data = null, editing = null, devices = [], search = '';
  const list = h('div', { class: 'protocols-list' });
  const form = h('div', { class: 'connection-form' });
  const status = h('p', { class: 'board-status', role: 'status' });
  const say = (text) => { status.textContent = text; };

  function rowText(conn) {
    const s = summary(conn, data.status[conn.id], Date.now() / 1000);
    if (s.state === 'ok' && s.ago === null) return t('connConnected');
    if (s.state === 'ok') { const [unit, n] = agoParts(s.ago); return t(`connSent.${unit}`, { n }); }
    if (s.state === 'error') return t('connError', { message: s.message });
    return t(s.state === 'paused' ? 'connPaused' : s.reason === 'noDevices' ? 'connNoDevices' : 'connStarting');
  }

  function drawList() {
    const rows = data.connections.map((conn) => {
      const connector = data.connectors.find((c) => c.type === conn.type);
      const state = summary(conn, data.status[conn.id], Date.now() / 1000).state;
      return h('div', { class: 'protocol-row', dataset: { active: String(state === 'ok') } },
        h('strong', {}, `${connector?.icon ?? '🔗'} ${conn.name}`),
        h('span', { class: 'brain-note' }, `${connector?.name ?? conn.type} · ${t('connDevices', { n: conn.devices.length })}`),
        h('span', { class: 'brain-note' }, `${MARK[state]} ${rowText(conn)}`),
        h('button', { type: 'button', class: 'blocks-button', 'aria-label': t('connEdit', { name: conn.name }),
          onclick: () => edit(structuredClone(conn)) }, '⚙'));
    });
    fill(list, rows.length ? rows : h('p', { class: 'studio-empty' }, t('connEmpty')));
  }

  function field(conn, option) {
    const input = h('input', { class: 'talk-input', type: option.type === 'number' ? 'number' : 'text',
      value: conn.options[option.key] ?? '', 'aria-label': t(`connOpt.${option.key}`) });
    input.addEventListener('change', () => {
      conn.options[option.key] = option.type === 'number' ? Number(input.value) : input.value.trim();
    });
    return h('label', { class: 'talk-input-label' }, t(`connOpt.${option.key}`), input);
  }

  function deviceRow(conn, device) {
    const shared = conn.devices.find((d) => d.entity_id === device.entity_id);
    const box = h('input', { type: 'checkbox', checked: Boolean(shared), 'aria-label': device.name,
      onchange: () => { Object.assign(conn, share(conn, device.entity_id, box.checked)); drawForm(); } });
    const extra = shared ? [
      h('input', { class: 'talk-input', value: shared.remote_id, 'aria-label': t('connRemoteId'),
        onchange: (e) => { shared.remote_id = e.target.value.trim(); } }),
      h('select', { class: 'talk-input', 'aria-label': t('connDirection'),
        onchange: (e) => { shared.direction = e.target.value; } },
      ['send', 'both'].map((d) => h('option', { value: d, selected: shared.direction === d }, t(`connDir.${d}`))))] : [];
    return h('div', { class: 'connection-device' }, h('label', { class: 'board-check' }, box, device.name), ...extra);
  }

  function drawForm() {
    if (!editing) { fill(form); return; }
    const conn = editing;
    const connector = data.connectors.find((c) => c.type === conn.type);
    const name = h('input', { class: 'talk-input', value: conn.name, 'aria-label': t('connName'),
      onchange: (e) => { conn.name = e.target.value.trim(); } });
    const find = h('input', { class: 'talk-input', type: 'search', value: search, placeholder: t('connSearch'),
      'aria-label': t('connSearch'), oninput: (e) => { search = e.target.value.toLowerCase(); drawForm(); find.focus(); } });
    const isShared = (d) => conn.devices.some((s) => s.entity_id === d.entity_id);
    const shown = [...devices.filter(isShared),  // the shared ones first, always visible
      ...devices.filter((d) => !isShared(d) && `${d.name} ${d.entity_id}`.toLowerCase().includes(search))].slice(0, MAX_LISTED);
    const isNew = !data.connections.some((c) => c.id === conn.id);
    const kind = isNew && data.connectors.length > 1
      ? h('label', { class: 'talk-input-label' }, t('connType'), h('select', { class: 'talk-input', 'aria-label': t('connType'),
        onchange: (e) => {
          const next = data.connectors.find((c) => c.type === e.target.value);
          editing = { ...draft(next, conn.name, data.connections.map((c) => c.id)), devices: conn.devices };
          drawForm();
        } }, data.connectors.map((c) => h('option', { value: c.type, selected: c.type === conn.type }, c.name))))
      : null;
    fill(form,
      h('h3', {}, `${connector?.icon ?? '🔗'} ${connector?.name ?? conn.type}`), kind,
      h('label', { class: 'talk-input-label' }, t('connName'), name),
      (connector?.options ?? []).map((option) => field(conn, option)),
      h('p', { class: 'talk-input-label' }, t('connShares')), find,
      devices.length ? shown.map((d) => deviceRow(conn, d)) : h('p', { class: 'brain-note' }, t('connNoHa')),
      h('div', { class: 'shop-actions' },
        h('button', { type: 'button', class: 'blocks-button', onclick: () => save(conn) }, t('connSave')),
        h('button', { type: 'button', class: 'blocks-button', onclick: () => save({ ...conn, enabled: !conn.enabled }) },
          t(conn.enabled ? 'connPause' : 'connResume')),
        data.connections.some((c) => c.id === conn.id)
          ? h('button', { type: 'button', class: 'blocks-button', onclick: () => remove(conn.id) }, t('connDelete')) : null,
        h('button', { type: 'button', class: 'blocks-button', onclick: () => { editing = null; drawForm(); } }, t('connClose'))));
  }

  function edit(conn) { editing = conn; search = ''; drawForm(); form.scrollIntoView?.({ block: 'nearest' }); }

  function add() {
    const connector = data.connectors[0];
    if (!connector) { say(t('connNoConnectors')); return; }
    edit(draft(connector, t('connNewName'), data.connections.map((c) => c.id)));
  }

  async function call(path, body) {
    try {
      data = await api(path, body);
      say(data.issues.map((i) => `⚠ ${i.message}`).join(' '));
      return true;
    } catch (error) {
      say(`⚠ ${error.message ?? error.code}`);
      return false;
    }
  }

  async function save(conn) {
    const taken = data.connections.map((c) => c.id);
    if (!taken.includes(conn.id)) conn = { ...conn, id: uniqueId(conn.name, taken) };  // a new one is named after its name
    if (await call('connections', conn)) { editing = null; say(t('connSaved')); }
    drawList(); drawForm();
  }

  async function remove(id) {
    if (!confirm(t('connConfirmDelete'))) return;
    if (await call(`connections/${encodeURIComponent(id)}/delete`, {})) editing = null;
    drawList(); drawForm();
  }

  async function poll() {
    if (!alive) return;
    if (await call('connections')) drawList();
    timer = setTimeout(poll, POLL_MS);
  }

  async function loadDevices() {
    try {
      const assist = await connectHa(t('connNoHa'));
      devices = shareable(await assist.request({ type: 'get_states' }));
      assist.close?.();
      drawForm();
    } catch (error) {
      say(`⚠ ${error.message ?? t('connNoHa')}`);
    }
  }

  return {
    id: 'connections', title: t('blockConnections'), icon: '🌐', defaultVisible: true, defaultColumn: 'main', optionsSchema: [],
    render(container) {
      alive = true;  // the block manager calls destroy() before every render
      fill(container, h('div', { class: 'shop-actions' },
        h('button', { type: 'button', class: 'blocks-button', onclick: add }, t('connAdd')),
        h('a', { class: 'blocks-button', href: '#/modulos' }, t('connInstallConnector'))), list, form, status,
      h('p', { class: 'board-status' }, t('connHint')));
      poll();
      loadDevices();
    },
    destroy() { alive = false; clearTimeout(timer); },
  };
}
