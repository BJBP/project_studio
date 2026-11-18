// Entry point of the voice demo: loads config + catalog, wires the stack and mounts blocks.
// On any failure the page still works in offline mode (local state only, no HA/MQTT).

import { loadConfig } from '../infrastructure/config.js';
import { oledFromState } from '../application/oled-text.js';
import { validateCatalog } from '../domain/catalog.js';
import { initialState } from '../domain/device-state.js';
import { mountBlocks } from '../../../../engines/blocks/block-manager.js';
import { createStorage } from '../../../../engines/blocks/storage.js';
import { createLiveStore } from './live.js';
import { createStack } from './stack.js';
import { syncAliases } from '../application/sync-aliases.js';
import { createBrainChoice } from '../application/brain-choice.js';
import { saveAiKey } from '../infrastructure/ai-keys.js';
import { createDemoBlocks } from './blocks/index.js';
import { createSimulator } from '../application/simulator.js';
import { t, localeTable } from './i18n.js';

// ?catalog=<name> loads data/<name>.json (video intercom, industry…); without it, the tutorial circuit.
const CATALOG_NAME = /^[a-z0-9_-]+$/.test(new URLSearchParams(location.search).get('catalog') ?? '')
  ? new URLSearchParams(location.search).get('catalog') : 'devices.example';
const DISCOVERY_SETTLE_MS = 2000; // HA needs a moment to register freshly announced entities
const BRAIN_STORAGE_KEY = 'studio.voice.brain';

// Remembers the chosen AI in this browser; private windows may block storage, the page still works.
const brainStore = {
  get() { try { return localStorage.getItem(BRAIN_STORAGE_KEY); } catch (err) { console.warn('voice demo: sin almacenamiento local', err); return null; } },
  set(id) { try { localStorage.setItem(BRAIN_STORAGE_KEY, id); } catch (err) { console.warn('voice demo: sin almacenamiento local', err); } },
};

const setIndicator = (id, up) => {
  const element = document.getElementById(`indicator-${id}`);
  if (!element) return;
  element.dataset.state = up ? 'up' : 'down';
  const status = element.querySelector('[data-role="status"]');
  if (status) status.textContent = up ? t('statusConnected') : t('statusDisconnected');
};

function applyStaticTexts() {
  document.title = t('appTitle');
  document.querySelector('.app-title').textContent = t('appName');
  document.querySelector('.app-subtitle').textContent = t('projectName');
  document.querySelector('.app-indicators')?.setAttribute('aria-label', t('projectName'));
  for (const [id, key] of [['ha', 'indicatorHA'], ['mqtt', 'indicatorMQTT'], ['mic', 'indicatorMic']]) {
    const label = document.getElementById(`indicator-${id}`)?.querySelector('[data-role="label"]');
    if (label) label.textContent = t(key);
  }
}

function showWarning(detail) {
  const warning = document.getElementById('config-warning');
  warning.textContent = '';
  const title = document.createElement('strong');
  title.textContent = `${t('configWarningTitle')}. `;
  const body = document.createElement('span');
  body.textContent = `${detail} ${t('offlineHint')}`;
  warning.append(title, body);
  warning.hidden = false;
}

async function loadCatalog() {
  try {
    const response = await fetch(`data/${CATALOG_NAME}.json`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    const result = validateCatalog(data);
    if (!result.ok) {
      showWarning(`${t('catalogError')} ${result.errors.map((e) => e.message).join(' · ')}`);
      return null;
    }
    return data;
  } catch (error) {
    showWarning(`${t('catalogError')} ${error?.message ?? error}`);
    return null;
  }
}

async function main() {
  applyStaticTexts();

  const config = await loadConfig();
  const offline = Boolean(config.error);
  if (offline) showWarning(config.error);

  const catalog = await loadCatalog();
  const live = createLiveStore(catalog ? initialState(catalog) : {});
  live.oled = oledFromState(live.state, '');
  const refreshOled = () => { live.oled = oledFromState(live.state, live.answer); };

  let brainChoice = null;
  const { virtualDevice, session, speaker, assist } = await createStack({
    catalog, offline, config, live, refreshOled, onIndicator: setIndicator,
    onAssistError: () => brainChoice?.fallBackToLocal() ?? false,
  });
  brainChoice = createBrainChoice({
    assist, session, providers: config.aiProviders, saveKey: saveAiKey, store: brainStore,
    onChange: ({ current }) => { live.brain = current; live.emit(); },
  });
  await brainChoice.load().catch((error) => console.warn('voice demo: no se pudieron leer las IAs', error));

  const simulator = virtualDevice ? createSimulator({ catalog, virtualDevice }) : null;
  const blocks = createDemoBlocks({ live, t, session, speaker, brainChoice, catalog, virtualDevice, simulator, assist });

  mountBlocks(document.getElementById('blocks-root'), {
    blocks,
    columns: [
      { id: 'main', title: t('columnMain') },
      { id: 'side', title: t('columnSide') },
    ],
    storage: createStorage(`studio.voice.layout.${CATALOG_NAME}`),
    t: localeTable,
  });

  if (virtualDevice) {
    try {
      await virtualDevice.start();
      simulator.start();
      if (assist) setTimeout(() => nameEntities(assist, catalog), DISCOVERY_SETTLE_MS);
    } catch (error) {
      console.warn('voice demo: no se pudo publicar el dispositivo virtual', error);
    }
  }

  window.addEventListener('beforeunload', () => { simulator?.stop(); virtualDevice?.stop(); });
  listenToStudio(live, session);
}

// Inside the Studio (?embed): no page header, and the guided tour can give orders like a person typing.
function listenToStudio(live, session) {
  if (new URLSearchParams(location.search).has('embed')) document.body.classList.add('is-embedded');
  window.addEventListener('message', (event) => {
    if (event.origin !== location.origin || event.data?.type !== 'studio-order') return;
    const text = String(event.data.text ?? '').trim();
    if (!text) return;
    live.addMessage('user', text);
    session.sendText(text);
  });
  window.studioDemoReady = true;
}

function nameEntities(assist, catalog) {
  syncAliases({ assist, catalog }).catch((error) => console.warn('voice demo: no se pudieron poner los nombres cortos', error));
}

main().catch((error) => {
  console.error('voice demo: fallo al arrancar', error);
  showWarning(error?.message ?? String(error));
});
