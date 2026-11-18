// Hardware block: each real ESP32 of the project with its pieces. ⚙ Compilar builds the firmware in Docker,
// ⚡ Instalar flashes it over USB from the browser and asks for the Wi-Fi (ESP Web Tools + Improv Serial),
// ✅ Probar opens the project's Tutorial tab (its «Pruébalo» checks), ↻ OTA opens the ESPHome dashboard for wireless updates.
import { fill, h } from '../../../shared/dom.js';

const ESP_WEB_TOOLS = 'https://unpkg.com/esp-web-tools@10.0.1/dist/web/install-button.js?module';
const ESPHOME_DASHBOARD = 'http://127.0.0.1:6052/';
const POLL_MS = 5000;

async function postJson(url, body) {
  const response = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  return response.json();
}

export function createHardwareBlock({ t, store, projectId }) {
  const timers = new Set();
  let toolsLoaded = null;

  const loadTools = () => (toolsLoaded ??= import(ESP_WEB_TOOLS).catch((error) => {
    toolsLoaded = null;
    throw error;
  }));

  function deviceCard(device) {
    const status = h('p', { class: 'brain-note', role: 'status' }, t('loading'));
    const install = h('div', { class: 'hw-install' });
    const build = h('button', { type: 'button', class: 'blocks-button' }, t('hwBuild'));

    async function refresh() {
      const state = await (await fetch(`/api/firmware/status/${device.firmware}`)).json();
      status.textContent = state.state === 'running' || state.state === 'error' ? state.message
        : state.ready ? t('hwReady') : t('hwNotBuilt');
      build.disabled = state.state === 'running';
      if (state.state === 'running') timers.add(setTimeout(refresh, POLL_MS));
      showInstall(state.ready);
    }

    async function showInstall(ready) {
      if (!ready) { fill(install); return; }
      if (!('serial' in navigator)) { fill(install, h('p', { class: 'lic-warn' }, t('hwNoSerial'))); return; }
      try {
        await loadTools();
        const button = document.createElement('esp-web-install-button');
        button.setAttribute('manifest', `/firmware/${device.firmware}/manifest.json`);
        button.append(h('button', { slot: 'activate', type: 'button', class: 'blocks-button' }, t('hwInstall')));
        fill(install, button, h('p', { class: 'brain-note' }, t('hwWifiHint')));
      } catch (error) {
        fill(install, h('p', { class: 'lic-warn' }, t('hwToolsOffline')));
      }
    }

    build.addEventListener('click', async () => {
      const state = await postJson('/api/firmware/build', { name: device.firmware });
      status.textContent = state.message;
      refresh();
    });
    refresh();
    const links = store.view.project.links ?? {};
    return h('section', { class: 'equipment-card' },
      h('h3', {}, `📟 ${device.name}`, h('span', { class: 'brain-note' }, ` · ${device.area}`)),
      h('p', { class: 'brain-note' }, t('hwPieces', { pieces: device.pieces.join(', ') })),
      status,
      h('div', { class: 'shop-actions' }, build, install,
        links.tutorial ? h('a', { class: 'blocks-button', href: `#/p/${encodeURIComponent(projectId)}/tutorial` }, t('hwTest')) : null,
        h('a', { class: 'blocks-button', href: ESPHOME_DASHBOARD, target: '_blank', rel: 'noopener' }, t('hwOta'))));
  }

  return {
    id: 'hardware', title: t('blockHardware'), icon: '📟', defaultVisible: true, defaultColumn: 'main', optionsSchema: [],
    render(container) {
      const devices = store.view.project.devices ?? [];
      fill(container, devices.length ? devices.map(deviceCard) : h('p', { class: 'studio-empty' }, t('hwNone')),
        h('p', { class: 'brain-note' }, t('hwCable')));
    },
    destroy() { for (const timer of timers) clearTimeout(timer); timers.clear(); },
  };
}
