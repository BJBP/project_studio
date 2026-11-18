// Home: one card per project (status, pieces, licenses, progress) and "+ Nuevo" to copy one for a client.
import { h } from '../../shared/dom.js';
import { t } from '../../shared/i18n.js';
import { api } from './api.js';

const LICENSE_TEXT = { ok: 'licensesOk', warn: 'licensesWarn', error: 'licensesError' };

function card(project) {
  const [done, total] = project.progress;
  return h('a', { class: 'studio-card', href: `#/p/${encodeURIComponent(project.id)}/arquitectura`, dataset: { id: project.id } },
    h('span', { class: 'studio-card-icon', 'aria-hidden': 'true' }, project.icon),
    h('strong', { class: 'studio-card-name' }, project.name),
    h('span', { class: 'studio-card-summary' }, project.summary),
    h('span', { class: `studio-badge status-${project.status}` }, t(`status.${project.status}`)),
    h('span', { class: 'studio-card-meta' },
      t('cardPieces', { n: project.pieces }), ' · ',
      h('span', { class: `lic-${project.licenses}` }, t(LICENSE_TEXT[project.licenses])),
      project.problems ? h('span', { class: 'lic-error' }, ' · ', t('cardProblems', { n: project.problems })) : null),
    h('span', { class: 'studio-progress', role: 'progressbar', 'aria-valuemin': 0, 'aria-valuemax': total, 'aria-valuenow': done,
      'aria-label': t('flowProgress') }, h('span', { style: `width:${total ? (100 * done) / total : 0}%` })),
    h('span', { class: 'studio-card-meta' }, t('cardProgress', { done, total })));
}

function newProjectForm(projects) {
  const name = h('input', { class: 'talk-input', required: true, placeholder: t('newNamePlaceholder'), id: 'new-name' });
  const from = h('select', { class: 'talk-input', id: 'new-from' },
    projects.map((p) => h('option', { value: p.id }, `${p.icon} ${p.name}`)));
  const message = h('p', { class: 'studio-error', role: 'alert', hidden: true });
  const form = h('form', { class: 'studio-new', hidden: true },
    h('label', { for: 'new-from' }, t('newFrom')), from,
    h('label', { for: 'new-name' }, t('newName')), name,
    h('button', { type: 'submit', class: 'blocks-button' }, t('newCreate')), message);
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      const { id } = await api('projects', { from: from.value, name: name.value });
      location.hash = `#/p/${encodeURIComponent(id)}/arquitectura`;
    } catch (error) {
      message.textContent = error.message;
      message.hidden = false;
    }
  });
  return form;
}

export async function renderHome(view) {
  const projects = await api('projects');
  const form = newProjectForm(projects);
  const toggle = h('button', { type: 'button', class: 'blocks-button', 'aria-expanded': 'false', id: 'btn-new' }, t('newProject'));
  toggle.addEventListener('click', () => {
    form.hidden = !form.hidden;
    toggle.setAttribute('aria-expanded', String(!form.hidden));
    if (!form.hidden) form.querySelector('input').focus();
  });
  view.append(
    h('div', { class: 'studio-heading' }, h('h1', {}, t('projectsTitle')), toggle),
    form,
    projects.length ? h('div', { class: 'studio-cards' }, projects.map(card)) : h('p', { class: 'studio-empty' }, t('projectsEmpty')));
  return null;
}
