// Reads what the voice assistant did, from Home Assistant's pipeline debug data. Pure: receives the data, returns
// plain objects. summarizeRun(run) -> { time, heard, answer, audioUrl, targets, error }; micLevel(states, deviceId)
// and satelliteState(states, deviceId) pick the board's microphone level and assistant step from get_states.

const TIME = { hour: '2-digit', minute: '2-digit', second: '2-digit' };

export function summarizeRun(run) {
  const summary = { time: '', heard: '', answer: '', audioUrl: '', targets: [], error: '' };
  for (const event of run?.events ?? []) {
    const data = event.data ?? {};
    if (event.type === 'run-start') summary.time = new Date(event.timestamp).toLocaleTimeString('es', TIME);
    if (event.type === 'stt-end') summary.heard = String(data.stt_output?.text ?? '').trim();
    if (event.type === 'intent-end') {
      const response = data.intent_output?.response ?? {};
      summary.answer = response.speech?.plain?.speech ?? '';
      summary.targets = (response.data?.success ?? []).map((target) => target.id);
    }
    if (event.type === 'tts-end') summary.audioUrl = data.tts_output?.url ?? '';
    if (event.type === 'error') summary.error = `${data.code ?? 'error'}: ${data.message ?? ''}`;
  }
  return summary;
}

const ofDevice = (states, domain, deviceId) =>
  states.filter((s) => s.entity_id.startsWith(`${domain}.${deviceId}_`) && !s.entity_id.includes('_virtual_'));

export function micLevel(states, deviceId) {
  const sensor = ofDevice(states, 'sensor', deviceId).find((s) => s.attributes?.device_class === 'sound_pressure');
  const value = Number(sensor?.state);
  return sensor && Number.isFinite(value) ? value : null;
}

export function satelliteState(states, deviceId) {
  return ofDevice(states, 'assist_satellite', deviceId)[0]?.state ?? null;
}
