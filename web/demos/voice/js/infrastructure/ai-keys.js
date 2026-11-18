// Sends a cloud AI key to the Studio server (serve.py), which stores it outside the repo and sets up the assistant.
// saveAiKey(provider, key) -> { ok, code, message }; the key never stays in the page.
export async function saveAiKey(provider, key) {
  try {
    const res = await fetch('/api/ai-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, key }),
    });
    const data = await res.json().catch(() => null);
    return data ?? { ok: false, code: 'E_STUDIO', message: `El Estudio rechazó la petición (${res.status}).` };
  } catch (err) {
    return { ok: false, code: 'E_STUDIO_DOWN', message: 'No responde el servidor del Estudio. ¿Sigue abierto iniciar_estudio.bat?' };
  }
}
