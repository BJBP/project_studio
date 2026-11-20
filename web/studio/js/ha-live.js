// Opens Home Assistant's WebSocket for a Studio block, with the token the Studio server gives in /config.json.
// connectHa() -> assist client ({ request, close }); throws { message } when Home Assistant is not configured.
import { createAssist } from '../../demos/voice/js/infrastructure/ha-assist.js';

export async function connectHa(noHaMessage) {
  const config = await (await fetch('/config.json')).json();
  if (config.error || !config.haToken) throw { message: config.error ?? noHaMessage };
  const assist = createAssist({ haUrl: config.haUrl, token: config.haToken });
  await assist.connect();
  return assist;
}
