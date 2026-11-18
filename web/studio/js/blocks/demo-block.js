// Demo block: the project's live demo (for the voice project, the voice demo page) inside the Studio.
// The guided tour sends it orders with postMessage({ type: 'studio-order', text }).
import { fill, h } from '../../../shared/dom.js';

export function createDemoBlock({ t, store }) {
  return {
    id: 'demo', title: t('blockDemo'), icon: '🎙️', defaultVisible: true, defaultColumn: 'main',
    optionsSchema: [{ key: 'height', label: t('optHeight'), type: 'number', default: 760, min: 400, max: 1400 }],
    render(container, options) {
      fill(container, h('iframe', {
        class: 'studio-demo-frame', src: store.view.project.links.demo, title: t('blockDemo'),
        style: `height:${Number(options.height) || 760}px`, allow: 'microphone; autoplay',
      }));
    },
  };
}
