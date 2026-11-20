# Project Studio — guía para agentes

Estudio de proyectos abiertos (domótica con voz local, videoportero, industrial). Plan completo y estado:
`docs/planes/estudio_proyectos.md`. Pendientes: `docs/backlog.md`. Fases 1 a 5 hechas; la 4b espera a la mini PC.

## Flujo de trabajo
1. Arrancar todo (stack de voz, Ollama, configuración de Home Assistant y Estudio), solo con Docker: doble clic en
   `iniciar_estudio.bat` / `iniciar_estudio.sh`, o en la raíz
   `docker compose --env-file stack/domotica-voz/.env --env-file .env run --rm init` (la primera vez) y
   `docker compose --env-file stack/domotica-voz/.env --env-file .env up -d`. La IA local: `COMPOSE_PROFILES` en
   `stack/domotica-voz/.env` (`cpu`, `gpu` o vacío para el Ollama del equipo con `OLLAMA_URL`).
2. Ver qué pasó al configurar Home Assistant: `docker compose logs setup` (`OK: ...` o `<CÓDIGO>: qué hacer`). El token
   queda en `~/.agents/secrets/project_studio/ha.json` (fuera del repo; un agente delegado no lo lee).
3. Placa por USB, modo cable y compilar firmware: fuera de Docker, con `uv` (`firmware/board.py`, `cable_bridge.py`,
   `build_firmware.py`); el Estudio en Docker no ve el puerto COM. Solo el stack: `docker compose -f
   stack/domotica-voz/docker-compose.yml up -d`.
4. Revisar un proyecto: `uv run --no-project python -m studio check <carpeta de datos> domotica-voz`
   → `OK: ...` o una línea `<CÓDIGO>: mensaje` por problema (salida 1 si hay errores `E_`).
   Exportar documentos: `... -m studio export <datos> <proyecto> <carpeta de salida>`.
5. Añadir una pieza = un JSON en `catalog/components/`; un proyecto = un JSON en `examples/projects/`.
   La carpeta de datos (`STUDIO_DATA`, por defecto `../project_studio_data`) guarda proyectos, avance y marcas.

## Mapa del código
| Zona | Archivos |
|---|---|
| Stack de voz (Docker) | `stack/domotica-voz/docker-compose.yml`, `mosquitto/mosquitto.conf`, `.env.example` |
| Configuración automática de Home Assistant | `stack/domotica-voz/setup/{setup_ha,flows,agents,ha_client}.py`; `ensure_host_paths.py` crea antes de Docker lo que montan los dos compose (datos, secretos, palabras para despertar, `esphome_secrets.yaml`); sin eso, los compose no arrancan (`create_host_path: false`) (`E_SECRETS_IS_DIR`, `E_NOT_WRITABLE`) |
| IAs disponibles (local y nube) | `stack/domotica-voz/ai_providers.json` (añadir una = añadir una entrada); claves en `~/.agents/secrets/project_studio/ai_keys.json` |
| Servidor del Estudio | `serve.py` (página, `/config.json`, audio), `serve_ai.py` (lista de IAs y guardar clave), `serve_models.py` (modelos de cada IA y cambio de modelo), `serve_wake.py` (palabra para despertar: elegir e importar), `serve_firmware.py` (compilar), `serve_board.py` (placa por USB: instalar, Wi-Fi, añadir a HA), `serve_jobs.py` (tareas largas) |
| Placa real por USB (sin navegador) | `uv run firmware/board.py ports` · `flash circuito_maestro --port COM4` · `status --port COM4` · `wifi --port COM4 [--stdin]` (lee `<secretos>/wifi.json`); líneas «@» en `firmware/cable.py`, puerto en `firmware/board_link.py`, firmware en `firmware/esphome/components/serial_bridge/`. Errores: `E_PORT_BUSY`, `E_FLASH`, `E_BOARD_SILENT`, `E_WIFI_FAILED`, `E_NO_WIFI_SECRETS`, `E_WIFI_FORMAT` |
| Funciones en la placa o en el PC (plan) | `docs/planes/funciones_placa_y_pc.md`: Home Assistant es el centro de los protocolos (KNX, Zigbee, Matter, Modbus…); el Estudio elige dónde corre cada función. Presentación: escenas 6 a 9 de `presentations/jefe.json` |
| Protocolos y puentes | Bloque «Protocolos» (`web/studio/js/blocks/protocols-block.js`, lista en `web/studio/protocols.json`); integraciones de la comunidad: `uv run stack/domotica-voz/setup/custom_integration.py sonoff` (lista en `custom_integrations.json`); Alexa y Google: `uv run stack/domotica-voz/setup/matterbridge.py install|start` o `serve_bridges.py` (`/api/bridge`). Errores: `E_DOWNLOAD`, `E_ARCHIVE`, `E_NO_NODE`, `E_NPM`, `E_NOT_INSTALLED`, `E_UNKNOWN_BRIDGE` |
| Placa autónoma | `firmware/esphome/packages/web_page.yaml` (página propia) y `local_rules.yaml` (botón, apagado por tiempo, horario); «Sin motor» en `oled.yaml`; secretos nuevos los añade `ensure_host_paths.py` |
| Modo cable (sin Wi-Fi) | `uv run firmware/cable_bridge.py --port COM4` anuncia «<aparato> (cable)» en HA por MQTT y pasa las órdenes; `--restore` lo quita. En el Estudio: «🔌 Por cable» en el bloque Placa. Plan: `docs/planes/modo_cable.md`. Errores: `E_MQTT_DOWN`, `E_PORT_LOST`, `AVISO E_HA_EXPOSE` |
| Activar por voz | servicio `wakeword` (microWakeWord) en el stack; `ha-assist.js` `startAudio(..., { wakeWord: true })`; `assistant-session.js` `startHandsFree()`; prueba: `tests/e2e/voice_pipeline.py --wake "Okey Nabu. Enciende el foco."` |
| Nombres real y virtual | `stack/domotica-voz/setup/device_names.py [proyecto]`: la placa toma el nombre elegido en «Qué hay conectado» (`state.json` → `names`), su gemelo virtual «… virtual» en el área Demo; `modes.py` hace que los modos actúen en los dos |
| Monitor de voz | `web/studio/js/blocks/voice-monitor-block.js` (nivel del micrófono, paso del asistente, últimas órdenes con ▶), datos en `web/studio/js/voice-runs.js`; el nivel sale del sensor `sound_level` de `packages/voice.yaml` |
| Gemelo digital | `web/studio/js/blocks/twin-block.js` (bloque en Aparatos) + `web/studio/js/twin-sync.js` (estados ↔ mensaje 3D, clic ↔ servicio de HA) + modo `?twin=1` del tutorial 3D (avisa los clics con `studio-twin-click`); conexión a HA en `web/studio/js/ha-live.js` |
| Tutorial 3D (copia del original) | `web/tutorials/circuito_3d/index.html` |
| Motor de bloques | `web/engines/blocks/` |
| Demo de voz (capas) | `web/demos/voice/js/{domain,application,infrastructure,presentation}/` |
| Estudio: reglas y casos de uso (Python, cebolla) | `studio/{domain,application,infrastructure,presentation}/` |
| Catálogo de piezas y equipos (repo, neutro) | `catalog/components/*.json`, `catalog/equipment/*.json` |
| Proyectos de ejemplo | `examples/projects/*.json` (se copian a la carpeta de datos la primera vez) |
| Pantallas del Estudio | `web/studio/` (Inicio, pestañas, bloques en `js/blocks/`), recorridos en `presentations/*.json` |
| Motores comunes | `web/engines/blocks/` (bloques), `web/engines/tour/` (Ayuda y Presentación), `web/shared/` |
| Pruebas | `tests/`: `node --test tests/*/*.test.mjs`; `uv run --no-project --with pytest --with httpx --with websockets pytest tests/server -q`; e2e en `tests/e2e/` |

## Códigos de error de setup_ha.py
`E_HA_DOWN`, `E_HA_HTTP`, `E_HA_AUTH`, `E_HA_WS`, `E_HA_ONBOARDED`, `E_FLOW_STEP`, `E_FLOW_ABORT`,
`E_AGENT`, `E_FLOW_INVALID` (clave rechazada), `E_ENTITY_MISSING`. Una IA de la nube que falla escribe
`AVISO <id> <CÓDIGO>: ...` y no detiene el resto. `serve_ai.py` añade `E_PROVIDER`, `E_KEY_FORMAT`, `E_SETUP`.

## Reglas del proyecto
- Código en inglés; textos de interfaz en `web/locales/es.json`.
- Puertos solo en 127.0.0.1. Ninguna marca, tienda ni precio en el repo: van en `../project_studio_data/`.
