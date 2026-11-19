// Digital twin block: the 3D circuit (tutorial page in ?twin=1 mode) mirrors the real board live, and a click on
// the relay, a 12V load or the buzzer acts on it through Home Assistant. Options: source (real or virtual) and
// what relay 1 drives (bulb or fan). Translation in ../twin-sync.js.
import { fill, h } from '../../../shared/dom.js';
import { connectHa } from '../ha-live.js';
import { twinAction, twinMessage } from '../twin-sync.js';

const POLL_MS = 1000;
const FAN_WORDS = /ventil|fan|cooler/i;  // a relay named like this is drawn as the fan

// What relay 1 drives, guessed from the name chosen in «Qué hay conectado»; the ⚙ options can change it.
function guessLoad(names, deviceId) {
  return FAN_WORDS.test(names?.[deviceId]?.foco ?? '') ? 'fan' : 'bulb';
}

export function createTwinBlock({ t, store }) {
  const device = (store.view.project.devices ?? [])[0];
  const timers = new Set();
  let assist = null, frame = null, lastStates = [], lastAlarm = null, alive = true, onMessage = null, current = {};
  const status = h('p', { class: 'board-status', role: 'status' });
  const say = (text, state) => { status.textContent = text; status.dataset.state = state ?? ''; };

  function later(fn, ms) {
    if (!alive) return;
    const id = setTimeout(() => { timers.delete(id); fn(); }, ms);
    timers.add(id);
  }

  function view(options) {
    return { source: options.source, load: options.load, header: device.name };
  }

  async function poll() {
    const options = current;
    try {
      lastStates = await assist.request({ type: 'get_states' });
      const message = twinMessage(lastStates, device.id, view(options));
      if (lastAlarm !== null && message.alarmStamp !== lastAlarm) message.alarma = true;
      lastAlarm = message.alarmStamp;
      frame?.contentWindow?.postMessage(message, location.origin);
      if (message.online) say(t(message.link === 'cable' ? 'twinOnlineCable' : message.link === 'wifi' ? 'twinOnlineWifi' : 'twinOnline'), 'ok');
      else say(t(options.source === 'real' ? 'twinOffline' : 'twinNoVirtual'), 'error');
    } catch (error) {
      say(`⚠ ${error.message ?? t('monitorNoHa')}`, 'error');
    }
    later(poll, POLL_MS);
  }

  async function act(part) {
    const action = twinAction(part, device.id, view(current), lastStates);
    if (!action || !assist) return;
    try {
      await assist.request({ type: 'call_service', domain: action.domain, service: action.service,
        target: { entity_id: action.entity_id } });
    } catch (error) {
      say(`⚠ ${error.message ?? error.code}`, 'error');
    }
  }

  return {
    id: 'twin', title: t('blockTwin'), icon: '🧿', defaultVisible: true, defaultColumn: 'main',
    optionsSchema: [
      { key: 'source', label: t('twinSource'), type: 'select', default: 'real',
        choices: [{ value: 'real', label: t('twinReal') }, { value: 'virtual', label: t('twinVirtual') }] },
      { key: 'load', label: t('twinLoad'), type: 'select', default: guessLoad(store.view.names, device?.id),
        choices: [{ value: 'bulb', label: t('twinBulb') }, { value: 'fan', label: t('twinFan') }] },
      { key: 'height', label: t('optHeight'), type: 'number', default: 560, min: 320, max: 1000 },
    ],
    render(container, options) {
      if (!device) { fill(container, h('p', { class: 'studio-empty' }, t('hwNone'))); return; }
      current = options;
      const page = store.view.project.links?.tutorial ?? '/tutorials/circuito_3d/index.html';
      frame = h('iframe', { class: 'studio-demo-frame', src: `${page}?twin=1`, title: t('blockTwin'),
        style: `height:${Number(options.height) || 560}px` });
      if (onMessage) window.removeEventListener('message', onMessage);
      onMessage = (event) => {
        if (event.origin === location.origin && event.source === frame.contentWindow && event.data?.type === 'studio-twin-click') {
          act(event.data.part);
        }
      };
      window.addEventListener('message', onMessage);
      fill(container, frame, h('p', { class: 'board-status' }, t('twinHint')), status);
      if (assist) return;
      connectHa(t('monitorNoHa')).then((client) => { assist = client; poll(); })
        .catch((error) => say(`⚠ ${error.message ?? t('monitorNoHa')}`, 'error'));
    },
    destroy() {
      alive = false;
      for (const timer of timers) clearTimeout(timer);
      timers.clear();
      if (onMessage) window.removeEventListener('message', onMessage);
      assist?.close?.();
    },
  };
}
