// Loads the AI choices and keeps the selected one in the assistant session.
// createBrainChoice({ assist, session, providers, saveKey, store, modelsApi })
//   -> { load, select, addKey, fallBackToLocal, loadModels, chooseModel, models(id) }.
// store: { get(), set(id) } remembers the choice; saveKey(provider, key) -> { ok, code, message };
// modelsApi: { fetch(provider) -> { models, current, gpuGb }, save(provider, model) -> { ok, code, message, current } }.
import { listBrains, pickBrain } from '../domain/brains.js';

export function createBrainChoice({ assist, session, providers, saveKey, store, onChange, modelsApi }) {
  let brains = [];
  let current = null;
  const modelInfo = new Map(); // provider id -> { models, current, gpuGb, saving, message }

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

  const notify = () => onChange?.({ brains, current });

  async function loadModels(providerId) {
    if (!modelsApi) return;
    const data = await modelsApi.fetch(providerId);
    modelInfo.set(providerId, data.models ? { ...data, message: null } : { models: [], message: data });
    notify();
  }

  // HA needs a moment to switch the assistant's model; the old one stays if the new one fails.
  async function chooseModel(providerId, model) {
    const info = modelInfo.get(providerId);
    if (!modelsApi || !info || info.saving) return null;
    modelInfo.set(providerId, { ...info, saving: model, message: null });
    notify();
    const result = await modelsApi.save(providerId, model);
    modelInfo.set(providerId, { ...info, current: result.current ?? info.current, saving: null, message: result.ok ? null : result });
    notify();
    return result;
  }

  const models = (providerId) => modelInfo.get(providerId) ?? null;

  return { load, select, addKey, fallBackToLocal, loadModels, chooseModel, models, get current() { return current; }, get brains() { return brains; } };
}
