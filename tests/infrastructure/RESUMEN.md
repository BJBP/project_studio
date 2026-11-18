# Resumen — capa de infraestructura de la demo de voz

Archivos creados (todos en `web/demos/voice/js/infrastructure/`, más las pruebas):

| Archivo | Qué hace |
|---|---|
| `config.js` | `loadConfig()` hace `fetch('/config.json')` y devuelve `{ haUrl, mqttUrl, haToken, error }`. Si el fetch falla o el HTTP no es 200, devuelve ese mismo objeto con `error` = `E_CONFIG: ...`. |
| `mqtt-bus.js` | `createMqttBus({ url, clientId, will })` sobre el global `mqtt`. `connect()` rechaza con `E_MQTT_DOWN` en 5 s; `payload` objeto → JSON; `subscribe` enruta por filtro con comodines `+` y `#`; `close()` cierra el cliente. Exporta además `topicMatches`. |
| `audio-convert.js` | `downsampleToInt16(float32Samples, inputRate, outputRate = 16000)` puro: promedio por bloques, recorte a −32768..32767, `Math.floor` del largo. Válida tasas y entrada. |
| `browser-mic.js` | `createBrowserMic({ onChunk, onLevel })`: `getUserMedia` (echoCancellation, noiseSuppression) → `AudioContext` → `AudioWorkletNode` `'studio-mic'` → convierte a Int16 16 kHz (`downsampleToInt16`) y calcula nivel (`rmsToDb`). Sin permiso rechaza con `E_MIC_DENIED`; fallo del worklet u otro error de captura → `E_MIC_UNAVAILABLE`. `stop()` libera pistas, nodo, ganancia y contexto. |
| `mic-worklet.js` | `AudioWorkletProcessor` registrado como `'studio-mic'`; envía cada bloque Float32 (copia) al hilo principal. |
| `ha-assist.js` | `createAssist({ haUrl, token, WebSocketImpl? })` → `{ connect, runText, startAudio, close }`. WebSocket a `<haUrl ws>/api/websocket`, auth `{type:'auth', access_token}`. `runText` usa `start_stage: 'intent'`; `startAudio` usa `stt` + `sample_rate: 16000` y, tras `run-start`, envía binarios `id byte + PCM Int16` (`end()` envía solo el byte). Encola trozos llegados antes de `run-start`. URLs TTS relativas se anteponen con `haUrl`. Token inválido → `E_HA_AUTH`; sin conexión o caída → `E_HA_DOWN`. |
| `speaker.js` | `createSpeaker({ onLevel })` → `{ play(url), setVolume(0..1), stop() }`. `Audio` + `AudioContext` + `MediaElementSource` + `AnalyserNode`; el nivel (dB vía `rmsToDb`) alimenta `onLevel` en cada frame para animar el amplificador virtual. Bloqueo del navegador → `E_AUDIO_BLOCKED` («Toca la página y repite»). Si el medio no es CORS-aprobado, reintenta una vez sin el grafo de Web Audio (audio suena, medidor no). |

Pruebas:

- `tests/infrastructure/audio-convert.test.mjs` — 48 kHz → 16 kHz, promedio por bloques, recorte, silencio, tasa por defecto, tasas inválidas.
- `tests/infrastructure/ha-assist.test.mjs` — lógica de mensajes con un `WebSocket` falso inyectable (`WebSocketImpl`): conversión http→ws, auth (`auth_ok` → resuelve, `auth_invalid` → `E_HA_AUTH`, error de conexión → `E_HA_DOWN`), despacho de eventos `stt-end` / `intent-end` / `tts-end` / `error` / `run-end`, URL TTS relativa y absoluta, tramas binarias con handler id, `end()`, y encolado antes de `run-start`.

Notas:

- Las capas `domain/` (creada por otro agente: `topics.js`, `audio-level.js`) se importan tal como se acordó; no se ha creado ni editado nada en esa carpeta.
- `browser-mic.js` y `speaker.js` importan `../domain/audio-level.js`; en el navegador funcionarán cuando el agente de dominio publique ese archivo.
- `speaker.js` marca `crossOrigin = 'anonymous'` para que el analizador reciba datos; si Home Assistant no envía cabeceras CORS para el TTS, el medio cae en el reintento directo y se oye igualmente (sin medidor). Anotarlo si se ve el medidor plano con TTS cross-origin.
- Sin commit, sin red externa, sin tocar archivos fuera de los creados aquí.

Salida de `node --test tests/infrastructure/*.test.mjs`:

```
ok 1 - 48 kHz -> 16 kHz: correct output length and averaged blocks
ok 2 - block averaging computes the mean of each ratio-sized block
ok 3 - clipping: out-of-range samples are clamped to Int16 bounds
ok 4 - silence produces all zeros
ok 5 - default output rate is 16000
ok 6 - invalid rates are rejected
ok 7 - connect() converts http->ws, authenticates and resolves on auth_ok
ok 8 - connect() rejects with E_HA_AUTH on auth_invalid
ok 9 - connect() rejects with E_HA_DOWN on connection error
ok 10 - runText() sends intent pipeline and dispatches stt/intent/tts/run-end events
ok 11 - runText() keeps absolute TTS URLs unchanged
ok 12 - startAudio() sends stt pipeline; sendChunk frames binary with handler id; end() sends the bare id
ok 13 - startAudio() queues chunks and end sent before run-start
ok 14 - error events are routed to onError with code and message
# tests 14
# pass 14
# fail 0
# duration_ms 108.4964
```
