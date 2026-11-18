// Asks the Studio server (serve_models.py) for the models of an AI and saves the chosen one.
// fetchModels(provider) -> { models, current, gpuGb } | { code, message };  saveModel(provider, model) -> { ok, code, message, current }.
const STUDIO_DOWN = { code: 'E_STUDIO_DOWN', message: 'No responde el servidor del Estudio. ¿Sigue abierto iniciar_estudio.bat?' };

export async function fetchModels(provider) {
  try {
    const res = await fetch(`/api/ai-models/${encodeURIComponent(provider)}`);
    return await res.json();
  } catch (err) {
    return STUDIO_DOWN;
  }
}

export async function saveModel(provider, model) {
  try {
    const res = await fetch('/api/ai-model', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, model }),
    });
    return await res.json();
  } catch (err) {
    return { ok: false, ...STUDIO_DOWN };
  }
}
