// Architecture diagram: one box per slot at its grid position, one line per connection with its protocol.
// Broken connections are dashed red. Click or Enter on a box selects that slot for the slot block.
import { fill } from '../../../shared/dom.js';

const SVG = 'http://www.w3.org/2000/svg';
const NODE_W = 150;
const NODE_H = 58;
const GAP_X = 44;
const GAP_Y = 46;

const svg = (tag, attrs = {}, text) => {
  const node = document.createElementNS(SVG, tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
};

const box = ([col, row]) => ({ x: col * (NODE_W + GAP_X), y: row * (NODE_H + GAP_Y) });
const center = (pos) => ({ x: box(pos).x + NODE_W / 2, y: box(pos).y + NODE_H / 2 });

function drawLine(root, conn, slots, broken) {
  const a = center(slots[conn.from].pos);
  const b = center(slots[conn.to].pos);
  const group = svg('g', { class: `diagram-line${broken ? ' is-broken' : ''}` });
  group.append(svg('line', { x1: a.x, y1: a.y, x2: b.x, y2: b.y }));
  const mid = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
  const width = conn.protocol.length * 7 + 12;
  group.append(svg('rect', { x: mid.x - width / 2, y: mid.y - 10, width, height: 20, rx: 10, class: 'diagram-label-bg' }),
    svg('text', { x: mid.x, y: mid.y + 4, 'text-anchor': 'middle', class: 'diagram-label' }, conn.protocol));
  root.append(group);
}

function drawNode(root, slot, choice, { t, store, problemSlots }) {
  const { x, y } = box(choice.pos);
  const name = choice.info?.name ?? choice.component;
  const group = svg('g', {
    class: `diagram-node${store.selected === slot ? ' is-selected' : ''}${problemSlots.has(slot) ? ' has-problem' : ''}`,
    tabindex: 0, role: 'button', 'data-slot': slot, 'aria-label': `${t(`slot.${slot}`)}: ${name}`,
  });
  group.append(svg('rect', { x, y, width: NODE_W, height: NODE_H, rx: 10 }),
    svg('text', { x: x + 12, y: y + 22, class: 'diagram-slot' }, t(`slot.${slot}`)),
    svg('text', { x: x + 12, y: y + 42, class: 'diagram-name' }, name.length > 20 ? `${name.slice(0, 19)}…` : name));
  group.addEventListener('click', () => store.select(slot));
  group.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); store.select(slot); }
  });
  root.append(group);
}

export function createDiagramBlock({ t, store }) {
  let unsubscribe = null;

  function render(container) {
    const { project, broken, issues } = store.view;
    const slots = project.slots;
    const positions = Object.values(slots).map((s) => s.pos);
    const width = (Math.max(...positions.map((p) => p[0])) + 1) * (NODE_W + GAP_X) - GAP_X;
    const height = (Math.max(...positions.map((p) => p[1])) + 1) * (NODE_H + GAP_Y) - GAP_Y;
    const root = svg('svg', { viewBox: `-8 -8 ${width + 16} ${height + 16}`, class: 'diagram', role: 'group',
      'aria-label': t('diagramLabel') });
    project.connections.forEach((conn, index) => drawLine(root, conn, slots, broken.includes(index)));
    const problemSlots = new Set(issues.map((i) => i.slot));
    for (const [slot, choice] of Object.entries(slots)) drawNode(root, slot, choice, { t, store, problemSlots });
    fill(container, root);
    container.querySelector(`[data-slot="${store.selected}"]`)?.setAttribute('aria-pressed', 'true');
  }

  return {
    id: 'diagram',
    title: t('blockDiagram'),
    icon: '🧩',
    defaultVisible: true,
    defaultColumn: 'main',
    optionsSchema: [],
    render(container) {
      render(container);
      unsubscribe?.();
      unsubscribe = store.subscribe(() => {
        const focused = document.activeElement?.dataset?.slot;
        render(container);
        if (focused) container.querySelector(`[data-slot="${focused}"]`)?.focus();
      });
    },
    destroy() { unsubscribe?.(); unsubscribe = null; },
  };
}
