// Wires the local stack (MQTT bus, HA Assist, mic, speaker, virtual device, session).
// createStack({ catalog, offline, config, live, refreshOled, onIndicator, onAssistError }) -> { virtualDevice, session, speaker, assist|null }.
// Falls back to a silent bus and an unavailable assist when the stack is down.

import { createMqttBus } from '../infrastructure/mqtt-bus.js';
import { createAssist } from '../infrastructure/ha-assist.js';
import { createBrowserMic } from '../infrastructure/browser-mic.js';
import { createSpeaker } from '../infrastructure/speaker.js';
import { createVirtualDevice } from '../application/virtual-device.js';
import { createAssistantSession } from '../application/assistant-session.js';
import { t } from './i18n.js';

const nullBus = { publish() {}, subscribe() {}, close() {} };
const unavailableAssist = {
  connect: () => Promise.reject({ code: 'E_HA_DOWN', message: t('stackDown') }),
  runText: () => { throw { code: 'E_HA_DOWN', message: t('stackDown') }; },
  startAudio: () => { throw { code: 'E_HA_DOWN', message: t('stackDown') }; },
  close() {},
};

// onAssistError(code) -> true when it switched to another AI (the message then says so).
export async function createStack({ catalog, offline, config, live, refreshOled, onIndicator, onAssistError }) {
  let bus = nullBus;
  if (!offline && config.mqttUrl) {
    const candidate = createMqttBus({ url: config.mqttUrl, clientId: `studio-voice-${Math.random().toString(16).slice(2, 10)}` });
    try {
      await candidate.connect();
      bus = candidate;
    } catch (error) {
      console.warn('voice demo: MQTT no disponible', error);
    }
  }
  onIndicator('mqtt', bus !== nullBus);

  let assist = unavailableAssist;
  if (!offline && config.haUrl) {
    const candidate = createAssist({ haUrl: config.haUrl, token: config.haToken });
    try {
      await candidate.connect();
      assist = candidate;
    } catch (error) {
      console.warn('voice demo: Home Assistant no disponible', error);
    }
  }
  onIndicator('ha', assist !== unavailableAssist);

  const handlers = {
    onStatus: (key) => {
      live.status = key;
      if (key === 'listening') onIndicator('mic', true);
      live.emit();
    },
    onHeard: (text) => live.addMessage('user', text),
    onAnswer: (text) => {
      live.error = null;
      live.answer = text;
      live.addMessage('assistant', text);
      refreshOled();
      live.emit();
    },
    onLevel: (db) => { live.level = db; live.emitLevel(); },
    onError: ({ code, message }) => {
      const isAssistFailure = !String(code ?? '').startsWith('E_MIC') && code !== 'E_EMPTY_INPUT';
      const switched = isAssistFailure && onAssistError?.(code);
      live.error = switched ? `${message || code} ${t('brainFallback')}` : (message || code);
      live.status = 'idle';
      if (String(code ?? '').startsWith('E_MIC')) onIndicator('mic', false);
      console.warn('voice demo:', code, message);
      live.emit();
    },
  };

  let session = null;
  const mic = createBrowserMic({
    onChunk: (chunk) => session?.forwardChunk(chunk),
    onLevel: (db) => handlers.onLevel(db),
  });
  const speaker = createSpeaker({ onLevel: (db) => handlers.onLevel(db) });

  const textKeys = new Set((catalog?.devices ?? []).flatMap((d) => d.entities
    .filter((e) => e.component === 'text').map((e) => `${d.id}/${e.key}`)));
  const virtualDevice = catalog ? createVirtualDevice({
    catalog,
    bus,
    onChange: (state, event) => {
      live.state = state;
      // Home Assistant writing the screen (an automation's warning) shows on the OLED like an answer.
      if (event.type === 'changed' && textKeys.has(`${event.deviceId}/${event.key}`)) live.answer = String(event.value);
      live.lastEvent = event;
      refreshOled();
      live.emit();
      live.lastEvent = null;
    },
  }) : null;

  session = createAssistantSession({ assist, mic, speaker, handlers });
  return { virtualDevice, session, speaker, assist: assist === unavailableAssist ? null : assist };
}
