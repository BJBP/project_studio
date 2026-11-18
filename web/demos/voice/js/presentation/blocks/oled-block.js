// OLED block: 256x128 canvas that renders live.oled (header + lines).
// Header yellow #facc15 at y=22 (16px), lines blue #38bdf8 at y=47+16*i (15px).

const WIDTH = 256;
const HEIGHT = 128;

export function createOledBlock({ live, t }) {
  let unsubscribe = null;

  function draw(canvas, scale) {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, WIDTH, HEIGHT);
    const oled = live.oled ?? { header: '', lines: [] };
    ctx.fillStyle = '#facc15';
    ctx.font = '16px "Courier New", monospace';
    ctx.fillText(oled.header ?? '', 8, 22);
    ctx.fillStyle = '#38bdf8';
    ctx.font = '15px "Courier New", monospace';
    (oled.lines ?? []).slice(0, 6).forEach((line, index) => {
      ctx.fillText(String(line), 8, 47 + 16 * index);
    });
    canvas.style.width = `${WIDTH * scale}px`;
    canvas.style.height = `${HEIGHT * scale}px`;
  }

  return {
    id: 'oled',
    title: t('blockOled'),
    icon: '🖥️',
    defaultVisible: true,
    defaultColumn: 'side',
    optionsSchema: [
      {
        key: 'scale',
        label: t('optScale'),
        type: 'select',
        default: '1x',
        choices: [
          { value: '1x', label: t('optScale1x') },
          { value: '2x', label: t('optScale2x') },
        ],
      },
    ],
    render(container, options) {
      const scale = options.scale === '2x' ? 2 : 1;
      const canvas = document.createElement('canvas');
      canvas.className = 'oled-canvas';
      canvas.width = WIDTH;
      canvas.height = HEIGHT;
      canvas.setAttribute('role', 'img');
      canvas.setAttribute('aria-label', t('blockOled'));
      container.append(canvas);
      draw(canvas, scale);
      unsubscribe?.();
      unsubscribe = live.subscribe(() => draw(canvas, scale));
    },
    destroy() {
      unsubscribe?.();
      unsubscribe = null;
    },
  };
}
