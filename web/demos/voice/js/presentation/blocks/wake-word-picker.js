// Wake word picker for the Talk block: the list of words (built in + own trained ones), «Importar palabra» for the
// trainer's .json + .tflite, and the result line. renderWakeWordPicker({ t, wakeWords }) -> HTMLElement.
import { readWakeWordFiles } from '../../infrastructure/wake-words.js';

export function renderWakeWordPicker({ t, wakeWords }) {
  const state = wakeWords.state;
  const box = document.createElement('div');
  box.className = 'talk-wake';

  const label = document.createElement('label');
  label.className = 'talk-input-label';
  label.textContent = t('wakeLabel');
  const select = document.createElement('select');
  select.className = 'talk-input';
  select.disabled = state.busy || !state.words.length;
  for (const word of state.words) {
    const text = word.own ? `${word.name} ${t('wakeOwn')}` : word.name;
    select.append(new Option(text, word.id, false, word.id === state.current));
  }
  select.addEventListener('change', () => wakeWords.choose(select.value));
  label.append(select);

  const files = document.createElement('input');
  files.type = 'file';
  files.accept = '.json,.tflite';
  files.multiple = true;
  files.hidden = true;
  files.addEventListener('change', async () => {
    const picked = await readWakeWordFiles(files.files);
    files.value = '';
    wakeWords.importFiles(picked);
  });
  const importButton = document.createElement('button');
  importButton.type = 'button';
  importButton.className = 'blocks-button';
  importButton.textContent = t('wakeImport');
  importButton.disabled = state.busy;
  importButton.title = t('wakeImportHint');
  importButton.addEventListener('click', () => files.click());

  const note = document.createElement('p');
  note.className = 'brain-key-message';
  note.setAttribute('role', 'status');
  if (state.busy) note.textContent = t('wakeSaving');
  else if (state.message) {
    note.textContent = state.message.ok ? state.message.message : `${state.message.code}: ${state.message.message}`;
    note.dataset.state = state.message.ok ? 'ok' : 'error';
  }

  box.append(label, importButton, files, note);
  return box;
}
