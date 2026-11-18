# Resumen — capa de aplicación y pantalla Demo (bloques) de la demo de voz

## Archivos creados

Aplicación (`web/demos/voice/js/application/`):

| Archivo | Qué hace |
|---|---|
| `virtual-device.js` | `createVirtualDevice({ catalog, bus, onChange })` → `{ start, command, getState, stop }`. `start` publica el discovery de `buildDiscovery`, `online` en `availabilityTopic` (retenido), el estado inicial de switches/text en `stateTopic` (retenido) y se suscribe a `${base}/+/+/set`. Cada mensaje → `parseCommandTopic` → `applyCommand`; si el evento es `changed` publica el nuevo valor retenido en `stateTopic` y llama `onChange(state, event)`. `command()` hace lo mismo sin tránsito MQTT y además lo publica. `stop()` publica `offline`. |
| `assistant-session.js` | `createAssistantSession({ assist, mic, speaker, handlers })` → `{ startTalking, stopTalking, sendText, forwardChunk }`. `startTalking`: `assist.startAudio(...)` + `mic.start()`; trozo de micrófono → `sendChunk`. `stopTalking`: `mic.stop()` + `end()`. `sendText`: `assist.runText` (texto vacío → error `E_EMPTY_INPUT` con «Escribe una orden primero»). Audio TTS → `speaker.play(url)`. Estados: `idle`, `listening`, `thinking` (tras STT y durante `runText`), `speaking`. Aunque no se pide en el contrato, exporta `forwardChunk(chunk)`: `browser-mic.js` fija sus callbacks al crearse, así que `main.js` enruta cada trozo del micrófono por ese método (ver backlog). |
| `oled-text.js` | `oledFromState(deviceState, answerText)` → cabecera `FOCO:ON  FAN:OFF` (switches `foco`/`cooler` del primer aparato; "FAN" es la etiqueta pedida para `cooler`) y cuerpo = texto de la última respuesta o «Listo. Di una orden». Usa `oledLayout` del dominio. |

Presentación (`web/demos/voice/`):

| Archivo | Qué hace |
|---|---|
| `index.html` | Carga `../../vendor/mqtt.min.js`, `../../engines/blocks/blocks.css`, `styles.css`, `voice-blocks.css` y `js/presentation/main.js` (module). Título «Estudio · Domótica con voz local». Cabecera con nombre del proyecto y tres indicadores (Home Assistant, MQTT, Micrófono) con estado Conectado / Sin conexión. |
| `styles.css` / `voice-blocks.css` | Variables CSS en `:root`, modo oscuro con `prefers-color-scheme`; cabecera, indicadores, aviso de configuración; estilos propios de los bloques. |
| `js/presentation/main.js` | `loadConfig()` → si `config.error`, aviso con el mensaje y modo sin conexión. Carga `data/devices.example.json`, valida con `validateCatalog`. Crea stack, bloques y los monta con `mountBlocks` (columnas `main` y `side`) + `createStorage('studio.voice.layout')`. |
| `js/presentation/stack.js` | Conexión con el stack: bus MQTT (con fallback a bus silencioso), Assist HA (con fallback a cliente no disponible), mic, speaker, dispositivo virtual, sesión y `handlers`. Actualiza los indicadores. Sin dependencias fuera de las capas inferiores. |
| `js/presentation/live.js` | Almacén compartido de UI: `state`, `answer`, `status`, `error`, `level`, `messages`, `subscribe` / `subscribeLevel`. |
| `js/presentation/i18n.js` | `t(key)` sobre `web/locales/es.json` (cargado con top-level await); exporta también `localeTable` para el motor de bloques. Clave ausente → la propia clave. |
| `js/presentation/blocks/circuit-block.js` | «Circuito 3D» (visible, `main`): iframe `../../tutorials/circuito_3d/index.html?embed=1`; en cada cambio de estado envía `postMessage({ type: 'studio-device', foco, cooler, alarma?, oledHeader, oledLines }, location.origin)` (`alarma: true` solo tras el evento `pressed` del botón `alarma`). Opción `height` (number, 300–900, defecto 520). |
| `js/presentation/blocks/oled-block.js` | «Pantalla OLED» (visible, `side`): canvas 256×128 negro; cabecera `#facc15` 16 px en y=22; líneas `#38bdf8` 15 px en y=47+16·i. Opción `scale` (select 1x/2x, `image-rendering: pixelated`). |
| `js/presentation/blocks/talk-block.js` | «Hablar» (visible, `side`): botón «Mantén para hablar» (pointerdown/up + `Space` con el botón enfocado), vúmetro en dB (`-60..0` → `0..100 %`), línea de estado aria-live (Listo / Escuchando… / Pensando… / Hablando…), campo «Escribe la orden» + «Enviar» con validación (vacío → «Escribe una orden primero»). Opciones `showTextInput` (boolean, true) y `volume` (number 0–100, 80; aplica `speaker.setVolume`). |
| `js/presentation/blocks/conversation-block.js` | «Conversación» (oculto por defecto): lista Tú / Asistente desde `live.messages`, scroll automático, estado vacío. Opción `maxMessages` (number, 20; min 1, max 100). |
| `js/presentation/blocks/devices-block.js` | «Aparatos» (oculto por defecto): filas por entidad con estado; switch → botón Encender/Apagar, button → «Probar»; llaman a `virtualDevice.command`. Sensor muestra valor o «Sin datos». |

`web/locales/es.json` (nuevo, único catálogo; el motor de bloques lee sus claves de ahí).

Pruebas: `tests/application/{virtual-device,assistant-session,oled-text}.test.mjs`.

## Verificación

- `node --test tests/application/*.test.mjs` → **9 tests, 9 pass, 0 fail** (ver abajo).
- Sintaxis de todos los módulos `.js` (`node --input-type=module --check`) y grafo de imports resueltos (sin imports rotos).
- `serve.py` sirve la página y todos los recursos con HTTP 200 (index, css, mqtt.min.js, módulos, es.json, devices.example.json, tutorial 3D, `/config.json`).
- El stack está arriba en esta máquina (HA en 8124, MQTT WS en 9002); no se tocó.
- Ningún commit; no se editó `js/domain/` (lo creó el agente del dominio, coincide con las firmas acordadas); sin red externa; sin secretos (no se leyó `ha.json`).

```
# tests 9
# pass 9
# fail 0
# duration_ms 135
```

Tests: discovery/disponibilidad/estado inicial retenidos al `start`; comando ON por MQTT → estado retenido publicado + `onChange`; `command()` sin tránsito MQTT publica igualmente; entidad desconocida → error sin publicar; `sendText` → `onAnswer` + `speaker.play(url)` + estados `thinking → speaking → idle`; `sendText` vacío → `E_EMPTY_INPUT`; `startTalking`/`stopTalking` → `listening → thinking`; `oledFromState` con foco ON → cabecera `FOCO:ON  FAN:OFF`; cuerpo por defecto «Listo. Di una orden».

## No probado / notas

- **Navegador real: NO verificado.** El navegador de este entorno bloquea cualquier URL local (`net::ERR_BLOCKED_BY_CLIENT` en `127.0.0.1` y `localhost`, puertos 8765 y 8766). No se instalaron otros navegadores. Verificado en su lugar: sintaxis, grafo de imports, HTTP 200 de todos los recursos y pruebas de nodo. **Falta abrir `http://127.0.0.1:8765/demos/voice/index.html` en un navegador normal con el stack en marcha** y comprobar: conexión de HA/MQTT, indicadores, bloques, voz real, vúmetro, iframe 3D y postMessage.
- **Flujo de voz real con HA sin probar** (micrófono → stt → intent → tts → altavoz): las piezas están cubiertas por las pruebas de infraestructura anteriores con dobles; falta la prueba de extremo a extremo.
- `assistant-session.js` expone `forwardChunk(chunk)` además del API pedido: `browser-mic.js` fíja sus callbacks al crearse y no acepta un setter, así que `main.js` enruta cada trozo por ese método. Anotado en `docs/backlog.md`.
- En modo sin conexión el dispositivo virtual se crea sobre un bus silencioso y Assist sobre un cliente no disponible: la página funciona (bloques, estado local, OLED) sin HA/MQTT, con los indicadores en «Sin conexión» y un aviso con el motivo.
- `live.lastEvent` se limpia tras cada `emit()` síncrono para que el `alarma: true` del postMessage no se repita en refrescos posteriores.
- `docs/backlog.md` actualizado (verificación en navegador, `forwardChunk`, pruebas de navegador pendientes).
- Servidores de prueba arrancados y detenidos durante la verificación; ninguno queda en marcha.
