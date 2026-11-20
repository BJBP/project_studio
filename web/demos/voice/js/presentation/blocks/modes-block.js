// Modes block: the circuit modes (voz, seguridad, salud, intercom, acústico) with their on/off switch in
// Home Assistant and a «Probar» button that simulates what triggers them (door, doorbell, heat, a bang).
import { fill, h } from '../../../../../shared/dom.js';

const DATA_URL = new URL('../../../data/', import.meta.url);

export function createModesBlock({ t, assist, simulator, catalog }) {
  let modes = [], states = {}, message = '', root = null;

  async function load() {
    try {
      modes = (await (await fetch(new URL(catalog?.modes ?? 'modes.example.json', DATA_URL))).json()).modes;
      await readStates();
    } catch (error) {
      message = t('modesLoadError');
      console.warn('modes: no se pudieron leer los modos', error);
    }
    if (root) render(root);
  }

  async function readStates() {
    if (!assist) return;
    const all = await assist.request({ type: 'get_states' });
    states = Object.fromEntries(all.filter((s) => s.entity_id.startsWith('input_boolean.modo_'))
      .map((s) => [s.entity_id.slice('input_boolean.modo_'.length), s.state === 'on']));
  }

  async function toggle(mode, on) {
    try {
      await assist.request({ type: 'call_service', domain: 'input_boolean', service: on ? 'turn_on' : 'turn_off',
        target: { entity_id: `input_boolean.modo_${mode.id}` } });
      states[mode.id] = on;
      message = '';
    } catch (error) {
      message = error.message ?? t('stackDown');
    }
    render(root);
  }

  function test(mode) {
    const problem = simulator?.pulse(mode.test.device, mode.test.key);
    message = problem ? t('modesTestError') : t('modesTesting', { name: mode.name });
    render(root);
  }

  function row(mode) {
    const on = mode.builtin || states[mode.id];
    const toggleBox = mode.builtin ? h('span', { class: 'brain-badge' }, t('modesAlways'))
      : h('input', { type: 'checkbox', role: 'switch', checked: on, disabled: !assist, 'aria-label': t('modesToggle', { name: mode.name }),
        onchange: (e) => toggle(mode, e.target.checked) });
    return h('li', { class: 'brain-row', dataset: { state: on ? 'current' : 'ready' } },
      h('div', { class: 'brain-text' }, h('strong', { class: 'brain-name' }, `${mode.icon} ${mode.name}`),
        h('span', { class: 'brain-note' }, mode.description)),
      toggleBox,
      mode.test ? h('button', { type: 'button', class: 'blocks-button', disabled: !on, onclick: () => test(mode) }, t('modesTest')) : null);
  }

  function render(container) {
    fill(container, modes.length ? h('ul', { class: 'brain-list' }, modes.map(row)) : h('p', {}, t('loading')),
      message ? h('p', { class: 'brain-note', role: 'status' }, message) : null);
  }

  return {
    id: 'modes', title: t('blockModes'), icon: '🧭', defaultVisible: false, defaultColumn: 'side', optionsSchema: [],
    render(container) { root = container; render(container); if (!modes.length) load(); },
    destroy() { root = null; },
  };
}
