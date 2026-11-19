// Voice monitor block: live microphone level of the real board, the assistant's step (waiting, listening,
// thinking, speaking) and its last orders (heard text, answer with ▶ to play it, what it moved). Reads Home
// Assistant over its WebSocket (token from /config.json); pure parsing in ../voice-runs.js.
import { fill, h } from '../../../shared/dom.js';
import { connectHa } from '../ha-live.js';
import { micLevel, satelliteState, summarizeRun } from '../voice-runs.js';

const LEVEL_MS = 1000;
const RUNS_MS = 3000;
const MAX_RUNS = 5;
const QUIET_DB = -80;
const LOUD_DB = -10;
const STEPS = ['idle', 'listening', 'processing', 'responding'];

export function createVoiceMonitorBlock({ t, store }) {
  const device = (store.view.project.devices ?? [])[0];
  const timers = new Set();
  const runCache = new Map();
  let assist = null;
  let alive = true;

  const bar = h('span', { class: 'monitor-bar' });
  const level = h('span', { class: 'monitor-db' }, '—');
  const steps = h('div', { class: 'monitor-steps' });
  const runs = h('div', { class: 'monitor-runs' });
  const status = h('p', { class: 'board-status', role: 'status' });
  const later = (fn, ms) => {
    if (!alive) return;
    const id = setTimeout(() => { timers.delete(id); fn(); }, ms);
    timers.add(id);
  };

  function showLevel(states) {
    const db = micLevel(states, device.id);
    const percent = db === null ? 0 : Math.max(0, Math.min(100, ((db - QUIET_DB) / (LOUD_DB - QUIET_DB)) * 100));
    bar.style.setProperty('--level', `${percent}%`);
    level.textContent = db === null ? t('monitorNoSignal') : `${db.toFixed(0)} dB`;
    level.dataset.state = db === null ? 'error' : '';
    const current = satelliteState(states, device.id);
    fill(steps, STEPS.map((step) => h('span', { class: 'monitor-step', 'aria-current': step === current ? 'step' : null },
      `${step === current ? '●' : '○'} ${t(`monitorStep_${step}`)}`)));
  }

  async function pollLevel() {
    try {
      showLevel(await assist.request({ type: 'get_states' }));
      say('');
    } catch (error) {
      say(`⚠ ${error.message ?? t('monitorNoHa')}`, 'error');
    }
    later(pollLevel, LEVEL_MS);
  }

  function runView(run) {
    return h('div', { class: 'monitor-run' },
      h('span', { class: 'monitor-time' }, run.time),
      h('div', {},
        h('p', {}, `🗣 «${run.heard || t('monitorNothingHeard')}»`),
        run.answer ? h('p', {}, `🤖 «${run.answer}»`,
          run.audioUrl ? h('button', { type: 'button', class: 'blocks-button', onclick: () => new Audio(run.audioUrl).play() }, t('monitorPlay')) : null) : null,
        run.targets.length ? h('p', { class: 'monitor-target' }, `→ ${run.targets.join(', ')}`) : null,
        run.error ? h('p', { class: 'lic-warn' }, `⚠ ${run.error}`) : null));
  }

  async function pollRuns() {
    try {
      const { preferred_pipeline: pipelineId } = await assist.request({ type: 'assist_pipeline/pipeline/list' });
      const { pipeline_runs: list } = await assist.request({ type: 'assist_pipeline/pipeline_debug/list', pipeline_id: pipelineId });
      const latest = list.slice(-MAX_RUNS).reverse();
      for (const item of latest.filter((r) => !runCache.has(r.pipeline_run_id))) {
        const run = await assist.request({ type: 'assist_pipeline/pipeline_debug/get', pipeline_id: pipelineId, pipeline_run_id: item.pipeline_run_id });
        runCache.set(item.pipeline_run_id, summarizeRun(run));
      }
      fill(runs, latest.length ? latest.map((r) => runView(runCache.get(r.pipeline_run_id))) : h('p', { class: 'studio-empty' }, t('monitorEmpty')));
    } catch (error) {
      say(`⚠ ${error.message ?? t('monitorNoHa')}`, 'error');
    }
    later(pollRuns, RUNS_MS);
  }

  function say(text, state) { status.textContent = text; status.dataset.state = state ?? ''; }

  return {
    id: 'voice-monitor', title: t('blockVoiceMonitor'), icon: '🎧', defaultVisible: true, defaultColumn: 'main', optionsSchema: [],
    render(container) {
      if (!device) { fill(container, h('p', { class: 'studio-empty' }, t('hwNone'))); return; }
      fill(container,
        h('div', { class: 'board-row' }, h('strong', {}, t('monitorMic')), bar, level),
        h('div', { class: 'board-row' }, h('strong', {}, t('monitorState')), steps),
        h('h4', {}, t('monitorRuns')), runs, status,
        h('p', { class: 'board-status' }, t('monitorHint')));
      connectHa(t('monitorNoHa')).then((client) => { assist = client; pollLevel(); pollRuns(); }).catch((error) => say(`⚠ ${error.message ?? t('monitorNoHa')}`, 'error'));
    },
    destroy() {
      alive = false;
      for (const timer of timers) clearTimeout(timer);
      timers.clear();
      assist?.close?.();
    },
  };
}
