// Keeps the wake word list and the chosen word; choosing or importing goes through the Studio server.
// createWakeWordChoice({ api, onChange }) -> { load, choose, importFiles, state }.
// state: { words, current, currentName, busy, message }  (message = { code, message } after a failure or an import).

export function createWakeWordChoice({ api, onChange }) {
  const state = { words: [], current: null, currentName: null, busy: false, message: null };

  function update(changes) {
    Object.assign(state, changes);
    state.currentName = state.words.find((w) => w.id === state.current)?.name ?? state.current;
    onChange?.(state);
  }

  async function load() {
    const data = await api.fetch();
    if (data.words) update({ words: data.words, current: data.current });
    else update({ message: data });
  }

  // HA needs a few seconds to switch its assistants to the new word; the old one stays if it fails.
  async function choose(word) {
    if (state.busy || word === state.current) return null;
    update({ busy: true, message: null });
    const result = await api.save(word);
    update({ busy: false, current: result.current ?? state.current, message: result.ok ? null : result });
    return result;
  }

  async function importFiles(files) {
    if (state.busy) return null;
    if (!files) {
      update({ message: { ok: false, code: 'E_WAKE_FILES', message: 'Elige los dos archivos del entrenador: el .json y el .tflite.' } });
      return null;
    }
    update({ busy: true, message: null });
    const result = await api.import(files);
    update({ busy: false, message: result });
    if (result.ok) await load();
    return result;
  }

  return { load, choose, importFiles, state };
}
