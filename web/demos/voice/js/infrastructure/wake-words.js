// Talks to the Studio server (serve_wake.py) about wake words: list, choose and import a trained one.
// wakeWordsApi = { fetch() -> { words, current }, save(word) -> { ok, code, message, current },
//                  import({ config, model }) -> { ok, code, message, id } }  (model = base64 of the .tflite).
const STUDIO_DOWN = { ok: false, code: 'E_STUDIO_DOWN', message: 'No responde el servidor del Estudio. ¿Sigue abierto iniciar_estudio.bat?' };

async function post(path, body) {
  try {
    const res = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    return await res.json();
  } catch (err) {
    return STUDIO_DOWN;
  }
}

export const wakeWordsApi = {
  async fetch() {
    try {
      return await (await fetch('/api/wake-words')).json();
    } catch (err) {
      return STUDIO_DOWN;
    }
  },
  save: (word) => post('/api/wake-word', { word }),
  import: (files) => post('/api/wake-word/import', files),
};

// The two files the trainer gives (.json + .tflite) as the server expects them.
export async function readWakeWordFiles(fileList) {
  const files = [...fileList];
  const config = files.find((f) => f.name.toLowerCase().endsWith('.json'));
  const model = files.find((f) => f.name.toLowerCase().endsWith('.tflite'));
  if (!config || !model) return null;
  const bytes = new Uint8Array(await model.arrayBuffer());
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return { config: await config.text(), model: btoa(binary) };
}
