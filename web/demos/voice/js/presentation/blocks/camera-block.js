// Camera block: the USB camera as a motion sensor (binary_sensor with sim "camera" in the catalog). The picture is
// analysed in the browser and never sent anywhere; only "movimiento ON/OFF" goes to Home Assistant.
import { fill, h } from '../../../../../shared/dom.js';
import { createCamera } from '../../infrastructure/browser-camera.js';
import { createMotionWatch } from '../../application/motion-watch.js';
import { SENSITIVITY } from '../../domain/motion.js';

const HOLD_S_DEFAULT = 10;

export function createCameraBlock({ t, catalog, virtualDevice }) {
  const target = (catalog?.devices ?? []).flatMap((d) => d.entities.map((e) => ({ device: d, entity: e })))
    .find(({ entity }) => entity.sim?.type === 'camera');
  let camera = null, running = false;

  function stop(status) {
    camera?.stop();
    camera = null;
    running = false;
    if (target) virtualDevice?.report(target.device.id, target.entity.key, 'OFF');
    if (status) status.textContent = t('cameraOff');
  }

  return {
    id: 'camera', title: t('blockCamera'), icon: '📷', defaultVisible: false, defaultColumn: 'main',
    optionsSchema: [{ key: 'sensitivity', label: t('optSensitivity'), type: 'select', default: 'medium',
      choices: Object.keys(SENSITIVITY).map((value) => ({ value, label: t(`sensitivity.${value}`) })) }],
    render(container, options) {
      if (!target) { fill(container, h('p', { class: 'brain-note' }, t('cameraNoSensor'))); return; }
      const video = h('video', { class: 'camera-video', muted: true, playsinline: true, 'aria-label': t('blockCamera') });
      const status = h('p', { class: 'talk-status', role: 'status' }, t('cameraOff'));
      const watch = createMotionWatch({
        threshold: SENSITIVITY[options.sensitivity] ?? SENSITIVITY.medium,
        holdMs: (target.entity.sim.pulse_s ?? HOLD_S_DEFAULT) * 1000,
        onChange: (on) => {
          virtualDevice?.report(target.device.id, target.entity.key, on ? 'ON' : 'OFF');
          status.textContent = on ? t('cameraMotion') : t('cameraStill');
        },
      });
      const button = h('button', { type: 'button', class: 'blocks-button' }, t('cameraStart'));
      button.addEventListener('click', async () => {
        if (running) { stop(status); watch.reset(); button.textContent = t('cameraStart'); return; }
        camera = createCamera({ onFrame: (gray) => watch.frame(gray) });
        try {
          await camera.start(video);
          running = true;
          button.textContent = t('cameraStop');
          status.textContent = t('cameraStill');
        } catch (error) {
          status.textContent = error.message;
          camera = null;
        }
      });
      fill(container, video, h('div', { class: 'shop-actions' }, button), status, h('p', { class: 'brain-note' }, t('cameraPrivacy')));
    },
    destroy() { stop(null); },
  };
}
