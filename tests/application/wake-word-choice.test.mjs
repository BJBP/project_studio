// Tests for the wake word choice: load, choose (keeps the old word on failure) and import. The server is a fake.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createWakeWordChoice } from '../../web/demos/voice/js/application/wake-word-choice.js';

function fakeApi() {
  const words = [{ id: 'okay_nabu', name: 'Okay Nabu', own: false }, { id: 'hey_jarvis', name: 'Hey Jarvis', own: false }];
  const api = {
    calls: [],
    ok: true,
    fetch: async () => ({ words: [...words], current: 'okay_nabu' }),
    save: async (word) => { api.calls.push(['save', word]); return api.ok ? { ok: true, current: word } : { ok: false, code: 'E_SETUP', message: 'x', current: 'okay_nabu' }; },
    import: async (files) => { api.calls.push(['import', files.config]); words.push({ id: 'oye_casa', name: 'Oye Casa', own: true }); return { ok: true, message: 'importada' }; },
  };
  return api;
}

test('choose switches the word and keeps the old one when HA fails', async () => {
  const api = fakeApi();
  const choice = createWakeWordChoice({ api });
  await choice.load();
  assert.equal(choice.state.currentName, 'Okay Nabu');
  await choice.choose('hey_jarvis');
  assert.equal(choice.state.currentName, 'Hey Jarvis');
  api.ok = false;
  await choice.choose('okay_nabu');
  assert.equal(choice.state.current, 'okay_nabu');
  assert.equal(choice.state.message.code, 'E_SETUP');
  assert.equal(await choice.choose('okay_nabu'), null, 'choosing the current word does nothing');
});

test('importFiles adds the word to the list; missing files give a clear message', async () => {
  const api = fakeApi();
  const changes = [];
  const choice = createWakeWordChoice({ api, onChange: (s) => changes.push(s.busy) });
  await choice.load();
  await choice.importFiles(null);
  assert.equal(choice.state.message.code, 'E_WAKE_FILES');
  assert.deepEqual(api.calls, []);
  await choice.importFiles({ config: '{}', model: 'AAAA' });
  assert.ok(choice.state.words.some((w) => w.id === 'oye_casa'));
  assert.ok(changes.includes(true), 'busy is shown while importing');
});
