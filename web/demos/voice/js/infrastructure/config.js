// Loads the page config served at /config.json (see serve.py).
// Returns { haUrl, mqttUrl, haToken, aiProviders, error }; on any failure `error` carries an E_... code.
export async function loadConfig() {
  try {
    const res = await fetch('/config.json');
    if (!res.ok) {
      return emptyConfig(`E_CONFIG: el servidor respondió ${res.status}. Recarga la página o ejecuta iniciar_estudio.bat.`);
    }
    const data = await res.json();
    return {
      haUrl: data.haUrl ?? null,
      mqttUrl: data.mqttUrl ?? null,
      haToken: data.haToken ?? null,
      aiProviders: Array.isArray(data.aiProviders) ? data.aiProviders : [],
      error: data.error ?? null,
    };
  } catch (err) {
    return emptyConfig('E_CONFIG: no se puede leer /config.json. ¿Está arrancado el Estudio con iniciar_estudio.bat?');
  }
}

function emptyConfig(error) {
  return { haUrl: null, mqttUrl: null, haToken: null, aiProviders: [], error };
}
