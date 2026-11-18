// Loads the AI choices and keeps the selected one in the assistant session.
// createBrainChoice({ assist, session, providers, saveKey, store }) -> { load, select, addKey, fallBackToLocal }.
// store: { get(), set(id) } remembers the choice; saveKey(provider, key) -> { ok, code, message }.
import { listBrains, pickBrain } from '../domain/brains.js';

export function createBrainChoice({ assist, session, providers, saveKey, store, onChange }) {
  let brains = [];
  let current = null;

  async function load(freshProviders = providers) {
    providers = freshProviders;
    const result = assist ? await assist.request({ type: 'assist_pipeline/pipeline/list' }) : { pipelines: [] };
    brains = listBrains(providers, result.pipelines);
    apply(pickBrain(brains, current?.id ?? store.get()));
  }

  function apply(brain) {
    current = brain;
    session.setPipeline(brain?.pipelineId ?? null);
    onChange?.({ brains, current });
  }

  function select(id) {
    const brain = brains.find((b) => b.id === id && b.status === 'ready');
    if (!brain) return;
    store.set(id);
    apply(brain);
  }

  // A cloud AI that fails (no internet, quota) gives way to the local one for the next order.
  function fallBackToLocal() {
    if (!current?.cloud) return false;
    const local = pickBrain(brains.filter((b) => !b.cloud), null);
    if (!local) return false;
    apply(local);
    return true;
  }

  async function addKey(providerId, key) {
    const result = await saveKey(providerId, key);
    if (result.ok) {
      providers = providers.map((p) => (p.id === providerId ? { ...p, hasKey: true } : p));
      await load(providers);
    }
    return result;
  }

  return { load, select, addKey, fallBackToLocal, get current() { return current; }, get brains() { return brains; } };
}
