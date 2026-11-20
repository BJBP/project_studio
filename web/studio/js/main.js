// Studio entry point: routes #/ (projects), #/p/<project>/<tab> and #/modulos, and starts the guided tours.
import { t } from '../../shared/i18n.js';
import { createTour } from '../../engines/tour/tour.js';
import { renderHome } from './home.js';
import { renderProject } from './project.js';
import { renderModules } from './modules-screen.js';
import { runAction, speak } from './tour-actions.js';

let current = null;

async function show() {
  current?.destroy?.();
  current = null;
  const view = document.getElementById('view');
  view.textContent = '';
  const [, page, projectId, tab] = location.hash.split('/');
  try {
    current = page === 'p' && projectId ? await renderProject(view, projectId, tab)
      : page === 'modulos' ? await renderModules(view) : await renderHome(view);
  } catch (error) {
    view.append(Object.assign(document.createElement('p'), {
      className: 'studio-error', role: 'alert', textContent: `${error.code ?? 'E_STUDIO'}: ${error.message ?? error}`,
    }));
  }
}

async function startTour(name) {
  try {
    const response = await fetch(`presentations/${name}.json`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const script = await response.json();
    tour.play(script.scenes);
  } catch (error) {
    console.warn('studio: no se pudo cargar la presentación', error);
  }
}

for (const node of document.querySelectorAll('[data-i18n]')) node.textContent = t(node.dataset.i18n);
const tour = createTour({ t, speak, runAction });
document.getElementById('btn-present').addEventListener('click', () => startTour('jefe'));
document.getElementById('btn-help').addEventListener('click', () => startTour('ayuda'));
window.addEventListener('hashchange', show);
show();
