// Board panel inside a device card: pick the USB port, install the firmware and give the board the Wi-Fi, all from
// this page (serve_board.py → firmware/board.py). The board lists the networks it sees; the password is only sent
// to the local server. createBoardPanel({ t, device, timers, projectId }) -> HTMLElement.
import { fill, h } from '../../../shared/dom.js';

const POLL_MS = 3000;

async function call(url, body) {
  const options = body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {};
  try {
    const response = await fetch(url, options);
    return await response.json();
  } catch (error) {
    return { code: 'E_STUDIO_DOWN', message: 'No responde el Estudio.' };
  }
}

const problem = (data) => (data?.code ? `⚠ ${data.message}` : null);

export function createBoardPanel({ t, device, timers, projectId }) {
  const port = h('select', { class: 'blocks-option-input', 'aria-label': t('boardPort') });
  const choices = h('datalist', { id: `board-networks-${device.firmware}` });
  const network = h('input', { class: 'blocks-option-input', list: choices.id, autocomplete: 'off', 'aria-label': t('boardNetwork') });
  const online = h('div', { class: 'shop-actions' });
  const password = h('input', { class: 'blocks-option-input', type: 'password', autocomplete: 'off', 'aria-label': t('boardPassword') });
  const remember = h('input', { type: 'checkbox', checked: true });
  const status = h('p', { class: 'board-status', role: 'status' });
  const say = (text, state) => { status.textContent = text ?? ''; status.dataset.state = state ?? ''; };
  const button = (key, onclick) => h('button', { type: 'button', class: 'blocks-button', onclick }, t(key));
  let savedSsid = null;

  async function loadPorts() {
    const data = await call('/api/board/ports');
    if (problem(data)) return say(problem(data), 'error');
    savedSsid = data.savedSsid;
    fill(port, data.ports.map((p) => new Option(t(p.connector === 'com' ? 'boardPortCom' : 'boardPortUsb', p), p.port)));
    say(data.ports.length ? '' : t('boardNoPorts'), data.ports.length ? '' : 'error');
    password.placeholder = savedSsid ? t('boardSavedHint', { ssid: savedSsid }) : '';
  }

  async function watchFlash() {
    const data = await call(`/api/board/flash/${encodeURIComponent(port.value)}`);
    say(data.message, data.state === 'error' ? 'error' : data.state === 'ok' ? 'ok' : '');
    if (data.state === 'running') timers.add(setTimeout(watchFlash, POLL_MS));
    if (data.state === 'ok') scanNetworks();
  }

  async function install() {
    if (!port.value) return say(t('boardNoPorts'), 'error');
    const data = await call('/api/board/flash', { name: device.firmware, port: port.value });
    if (problem(data)) return say(problem(data), 'error');
    watchFlash();
  }

  async function scanNetworks() {
    say(t('boardScanning'));
    fill(online);
    const data = await call('/api/board/scan', { port: port.value });
    if (problem(data)) return say(problem(data), 'error');
    fill(choices, data.networks.map((n) => new Option(`${n.secure ? '🔒' : ''} ${n.rssi} dBm`, n.ssid)));
    if (!network.value) network.value = data.networks[0]?.ssid ?? savedSsid ?? '';
    if (data.online) {
      fill(online, button('boardAddToHa', () => addToHa(data.ip)));
      return say(t('boardOnline', { ip: data.ip ?? '?' }), 'ok');
    }
    say(data.networks.length ? t('boardPickNetwork') : t('boardNoNetworks'), data.networks.length ? '' : 'error');
  }

  async function addToHa(ip) {
    say(t('boardAdding'));
    const data = await call('/api/board/ha', { ip, project: projectId });
    if (problem(data)) return say(problem(data), 'error');
    say(t(data.inHomeAssistant ? 'boardDone' : 'boardDoneNoHa', { ip: data.ip, message: data.message }), data.inHomeAssistant ? 'ok' : 'error');
  }

  async function connect() {
    if (!network.value.trim()) return say(t('boardPickNetwork'), 'error');
    say(t('boardConnecting'));
    const data = await call('/api/board/wifi', {
      port: port.value, ssid: network.value.trim(), remember: remember.checked, project: projectId,
      password: network.value === savedSsid && !password.value ? '' : password.value,
    });
    password.value = '';
    if (problem(data)) return say(problem(data), 'error');
    say(t(data.inHomeAssistant ? 'boardDone' : 'boardDoneNoHa', { ip: data.ip, message: data.message }), data.inHomeAssistant ? 'ok' : 'error');
  }

  const show = h('button', { type: 'button', class: 'blocks-button', 'aria-label': t('boardShowPassword'),
    onclick: () => { password.type = password.type === 'password' ? 'text' : 'password'; } }, '👁');
  loadPorts();
  return h('div', { class: 'board-panel' },
    h('label', { class: 'board-row' }, t('boardPort'), port, button('boardRefresh', loadPorts)),
    h('div', { class: 'shop-actions' }, button('boardInstall', install), button('boardScan', scanNetworks)),
    online,
    h('fieldset', { class: 'board-wifi' }, h('legend', {}, t('boardWifi')),
      h('label', { class: 'board-row' }, t('boardNetwork'), network, choices),
      h('label', { class: 'board-row' }, t('boardPassword'), password, show),
      h('label', { class: 'board-check' }, remember, t('boardRemember')),
      button('boardConnect', connect)),
    status);
}
