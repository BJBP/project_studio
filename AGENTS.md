# Project Studio — guía para agentes

Estudio de proyectos abiertos (domótica con voz local, videoportero, industrial). Plan completo y estado:
`docs/planes/estudio_proyectos.md`. Pendientes: `docs/backlog.md`. Fases 1 a 5 hechas; la 4b espera a la mini PC.

## Flujo de trabajo
1. Arrancar el stack: `docker compose -f stack/domotica-voz/docker-compose.yml up -d`.
2. Configurar Home Assistant (solo la primera vez): `uv run stack/domotica-voz/setup/setup_ha.py`.
   Devuelve `OK: ...` o `<CÓDIGO>: qué hacer`. El token queda en `~/.agents/secrets/project_studio/ha.json`
   (fuera del repo; un agente delegado no lo lee).
3. Abrir el Estudio: `iniciar_estudio.bat` (Windows) o `iniciar_estudio.sh`. Con Docker: `docker compose up -d`.
4. Revisar un proyecto: `uv run --no-project python -m studio check <carpeta de datos> domotica-voz`
   → `OK: ...` o una línea `<CÓDIGO>: mensaje` por problema (salida 1 si hay errores `E_`).
   Exportar documentos: `... -m studio export <datos> <proyecto> <carpeta de salida>`.
5. Añadir una pieza = un JSON en `catalog/components/`; un proyecto = un JSON en `examples/projects/`.
   La carpeta de datos (`STUDIO_DATA`, por defecto `../project_studio_data`) guarda proyectos, avance y marcas.

## Mapa del código
| Zona | Archivos |
|---|---|
| Stack de voz (Docker) | `stack/domotica-voz/docker-compose.yml`, `mosquitto/mosquitto.conf`, `.env.example` |
| Configuración automática de Home Assistant | `stack/domotica-voz/setup/{setup_ha,flows,agents,ha_client}.py` |
| IAs disponibles (local y nube) | `stack/domotica-voz/ai_providers.json` (añadir una = añadir una entrada); claves en `~/.agents/secrets/project_studio/ai_keys.json` |
| Servidor del Estudio | `serve.py` (página, `/config.json`, audio), `serve_ai.py` (lista de IAs y guardar clave), `serve_models.py` (modelos de cada IA y cambio de modelo), `serve_wake.py` (palabra para despertar: elegir e importar), `serve_firmware.py` (compilar), `serve_board.py` (placa por USB: instalar, Wi-Fi, añadir a HA), `serve_jobs.py` (tareas largas) |
| Placa real por USB (sin navegador) | `uv run firmware/board.py ports` · `flash circuito_maestro --port COM4` · `status --port COM4` · `wifi --port COM4 [--stdin]` (lee `<secretos>/wifi.json`); líneas «@» en `firmware/cable.py`, puerto en `firmware/board_link.py`, firmware en `firmware/esphome/components/serial_bridge/`. Errores: `E_PORT_BUSY`, `E_FLASH`, `E_BOARD_SILENT`, `E_WIFI_FAILED`, `E_NO_WIFI_SECRETS`, `E_WIFI_FORMAT` |
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
| Pruebas | `tests/`: `node --test tests/*/*.test.mjs`; `uv run --no-project --with pytest pytest tests/server -q`; e2e en `tests/e2e/` |

## Códigos de error de setup_ha.py
`E_HA_DOWN`, `E_HA_HTTP`, `E_HA_AUTH`, `E_HA_WS`, `E_HA_ONBOARDED`, `E_FLOW_STEP`, `E_FLOW_ABORT`,
`E_AGENT`, `E_FLOW_INVALID` (clave rechazada), `E_ENTITY_MISSING`. Una IA de la nube que falla escribe
`AVISO <id> <CÓDIGO>: ...` y no detiene el resto. `serve_ai.py` añade `E_PROVIDER`, `E_KEY_FORMAT`, `E_SETUP`.

## Reglas del proyecto
- Código en inglés; textos de interfaz en `web/locales/es.json`.
- Puertos solo en 127.0.0.1. Ninguna marca, tienda ni precio en el repo: van en `../project_studio_data/`.
