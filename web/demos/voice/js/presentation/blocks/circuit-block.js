// Circuit 3D block: embeds the 3D tutorial and mirrors the device state into it.
// Sends postMessage { type: 'studio-device', ... } to the iframe on every state change.

export function createCircuitBlock({ live, t }) {
  let unsubscribe = null;

  function deviceSnapshot() {
    const state = live.state ?? {};
    const first = state[Object.keys(state)[0]] ?? {};
    const snapshot = {
      type: 'studio-device',
      foco: String(first.foco ?? 'OFF').toUpperCase() === 'ON',
      cooler: String(first.cooler ?? 'OFF').toUpperCase() === 'ON',
      oledHeader: live.oled?.header ?? '',
      oledLines: live.oled?.lines ?? [],
    };
    if (live.lastEvent?.type === 'pressed' && live.lastEvent?.key === 'alarma') snapshot.alarma = true;
    return snapshot;
  }

  return {
    id: 'circuit',
    title: t('blockCircuit'),
    icon: '🔌',
    defaultVisible: true,
    defaultColumn: 'main',
    optionsSchema: [
      { key: 'height', label: t('optHeight'), type: 'number', default: 520, min: 300, max: 900 },
    ],
    render(container, options) {
      const iframe = document.createElement('iframe');
      iframe.className = 'circuit-frame';
      iframe.src = '../../tutorials/circuito_3d/index.html?embed=1';
      iframe.title = t('blockCircuit');
      iframe.style.height = `${Number(options.height) || 520}px`;
      iframe.addEventListener('load', () => iframe.contentWindow?.postMessage(deviceSnapshot(), location.origin));
      container.append(iframe);
      unsubscribe?.();
      unsubscribe = live.subscribe(() => iframe.contentWindow?.postMessage(deviceSnapshot(), location.origin));
    },
    destroy() {
      unsubscribe?.();
      unsubscribe = null;
    },
  };
}
