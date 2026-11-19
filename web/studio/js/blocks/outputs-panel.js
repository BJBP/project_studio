// «Qué hay conectado» inside a device card: one name per output of the board (the relay may drive a fan, not a
// lamp). Saves the name in the project (POST names) and renames it in Home Assistant (POST /api/device-names), so
// the voice uses it. createOutputsPanel({ t, device, projectId, names }) -> HTMLElement.
import { fill, h } from '../../../shared/dom.js';
import { api } from '../api.js';

const CATALOG_URL = '/demos/voice/data/devices.example.json';

async function catalogEntities(deviceId) {
  const response = await fetch(CATALOG_URL);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return (await response.json()).devices?.find((d) => d.id === deviceId)?.entities ?? [];
}

export function createOutputsPanel({ t, device, projectId, names }) {
  const rows = h('div', { class: 'board-panel' });
  const status = h('p', { class: 'board-status', role: 'status' });
  const say = (text, state) => { status.textContent = text; status.dataset.state = state ?? ''; };

  async function save(key, input) {
    say(t('namesSaving'));
    try {
      await api(`projects/${encodeURIComponent(projectId)}/names`, { device: device.id, key, name: input.value });
      const response = await fetch('/api/device-names', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ project: projectId }),
      });
      const result = await response.json();
      say(response.ok ? t('namesSaved') : `⚠ ${result.message}`, response.ok ? 'ok' : 'error');
    } catch (error) {
      say(`⚠ ${error.message ?? error}`, 'error');
    }
  }

  catalogEntities(device.id).then((entities) => {
    fill(rows, entities.map((entity) => {
      const input = h('input', {
        class: 'blocks-option-input', value: names?.[entity.key] ?? '', placeholder: entity.name, maxlength: 40,
        'aria-label': t('namesFor', { name: entity.name }),
      });
      input.addEventListener('change', () => save(entity.key, input));
      return h('label', { class: 'board-row' }, h('span', { class: 'names-key' }, entity.name), input);
    }));
  }).catch(() => say(t('namesNoCatalog'), 'error'));

  return h('details', { class: 'board-wifi' }, h('summary', {}, t('namesTitle')),
    h('p', { class: 'board-status' }, t('namesHint')), rows, status);
}
