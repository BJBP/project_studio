// Page blocks: a page of the project shown inside the Studio (project.links.<link>), with a full-screen button.
// Demo = the live demo (the guided tour sends it orders with postMessage({ type: 'studio-order', text }));
// Tutorial = the step-by-step breadboard tutorial in 3D.
import { fill, h } from '../../../shared/dom.js';

function createPageBlock({ t, store }, { id, link, titleKey, icon, height, allow }) {
  return {
    id, title: t(titleKey), icon, defaultVisible: true, defaultColumn: 'main',
    optionsSchema: [{ key: 'height', label: t('optHeight'), type: 'number', default: height, min: 400, max: 1400 }],
    render(container, options) {
      const frame = h('iframe', {
        class: 'studio-demo-frame', src: store.view.project.links[link], title: t(titleKey),
        style: `height:${Number(options.height) || height}px`, allow,
      });
      const full = h('button', { type: 'button', class: 'blocks-button', onclick: () => frame.requestFullscreen?.() }, t('pageFullscreen'));
      fill(container, h('div', { class: 'shop-actions' }, full), frame);
    },
  };
}

export const createDemoBlock = (ctx) => createPageBlock(ctx, {
  id: 'demo', link: 'demo', titleKey: 'blockDemo', icon: '🎙️', height: 760, allow: 'microphone; autoplay',
});

export const createTutorialBlock = (ctx) => createPageBlock(ctx, {
  id: 'tutorial', link: 'tutorial', titleKey: 'blockTutorial', icon: '🔌', height: 820, allow: 'fullscreen',
});
