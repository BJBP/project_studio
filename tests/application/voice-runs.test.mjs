// Voice monitor parsing: one Home Assistant pipeline run becomes heard text, answer, audio and targets;
// the board's microphone level and assistant step come from get_states, never from the virtual twin.
import test from 'node:test';
import assert from 'node:assert/strict';
import { micLevel, satelliteState, summarizeRun } from '../../web/studio/js/voice-runs.js';

test('a pipeline run is summarized for the monitor', () => {
  const run = { events: [
    { type: 'run-start', timestamp: '2026-11-19T20:19:26Z', data: {} },
    { type: 'stt-end', data: { stt_output: { text: ' apaga el foco' } } },
    { type: 'intent-end', data: { intent_output: { response: {
      speech: { plain: { speech: 'Se ha apagado el interruptor' } },
      data: { success: [{ id: 'switch.lab_virtual_foco' }] } } } } },
    { type: 'tts-end', data: { tts_output: { url: '/api/tts_proxy/a.mp3' } } },
  ] };
  const summary = summarizeRun(run);
  assert.equal(summary.heard, 'apaga el foco');
  assert.equal(summary.answer, 'Se ha apagado el interruptor');
  assert.deepEqual(summary.targets, ['switch.lab_virtual_foco']);
  assert.equal(summary.audioUrl, '/api/tts_proxy/a.mp3');
  assert.ok(summary.time);
});

test('an error run keeps the error and an empty run is safe', () => {
  assert.equal(summarizeRun({ events: [{ type: 'error', data: { code: 'stt-no-text-recognized', message: 'No text' } }] }).error,
    'stt-no-text-recognized: No text');
  assert.equal(summarizeRun(null).heard, '');
});

test('microphone level and step come from the real board only', () => {
  const states = [
    { entity_id: 'sensor.lab_virtual_mic', state: '-5', attributes: { device_class: 'sound_pressure' } },
    { entity_id: 'sensor.lab_mic', state: '-42.3', attributes: { device_class: 'sound_pressure' } },
    { entity_id: 'assist_satellite.lab_satelite_assist', state: 'listening', attributes: {} },
  ];
  assert.equal(micLevel(states, 'lab'), -42.3);
  assert.equal(satelliteState(states, 'lab'), 'listening');
  assert.equal(micLevel([{ entity_id: 'sensor.lab_mic', state: 'unknown', attributes: { device_class: 'sound_pressure' } }], 'lab'), null);
});
