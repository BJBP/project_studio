// The AIs ("brains") the assistant can think with. Receives the provider list from the Studio server and HA's
// voice pipelines; returns one entry per provider with its pipeline id and a status: ready | needs_key | not_ready.
export function listBrains(providers, pipelines) {
  return (providers ?? []).map((provider) => {
    const pipeline = (pipelines ?? []).find((p) => p.name === provider.pipeline);
    let status = 'ready';
    if (!pipeline) status = provider.cloud && !provider.hasKey ? 'needs_key' : 'not_ready';
    return { ...provider, pipelineId: pipeline?.id ?? null, status };
  });
}

// The brain to use: the saved choice when it is ready, otherwise the first ready local one, otherwise any ready one.
export function pickBrain(brains, savedId) {
  const ready = brains.filter((b) => b.status === 'ready');
  return ready.find((b) => b.id === savedId) ?? ready.find((b) => !b.cloud) ?? ready[0] ?? null;
}
