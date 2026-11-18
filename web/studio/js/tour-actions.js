// What the guided tours can do on the real Studio: speak with Piper, give a voice order to the demo,
// swap/reset/select a piece. Each action works on the real system (same API as the buttons).
import { api } from './api.js';

const DEMO_READY_MS = 8000;
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export async function speak(text) {
  const response = await fetch('/api/speak', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }),
  });
  if (!response.ok) return null;
  return (await response.json()).url ?? null;
}

async function demoFrame() {
  const deadline = Date.now() + DEMO_READY_MS;
  while (Date.now() < deadline) {
    const frame = document.querySelector('.studio-demo-frame');
    if (frame?.contentWindow?.studioDemoReady) return frame.contentWindow;
    await sleep(250);
  }
  throw new Error('la demo no está lista');
}

const ACTIONS = {
  async order({ text }) {
    const demo = await demoFrame();
    demo.postMessage({ type: 'studio-order', text }, location.origin);
  },
  async swap({ project, slot, component }) {
    await api(`projects/${encodeURIComponent(project)}/swap`, { slot, component });
    window.dispatchEvent(new CustomEvent('studio:refresh'));
    window.dispatchEvent(new CustomEvent('studio:select', { detail: slot }));
  },
  async reset({ project, slot }) {
    await api(`projects/${encodeURIComponent(project)}/reset`, { slot });
    window.dispatchEvent(new CustomEvent('studio:refresh'));
  },
  async select({ slot }) {
    window.dispatchEvent(new CustomEvent('studio:select', { detail: slot }));
  },
};

export async function runAction(action) {
  const handler = ACTIONS[action.type];
  if (!handler) throw new Error(`acción desconocida: ${action.type}`);
  await handler(action);
}
