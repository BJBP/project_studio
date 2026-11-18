# Project Studio — guía para agentes

Estudio de proyectos abiertos (domótica con voz local, videoportero, industrial). Plan completo y estado:
`docs/planes/estudio_proyectos.md`. Pendientes: `docs/backlog.md`. Fase actual: **1, demo de voz**.

## Flujo de trabajo
1. Arrancar el stack: `docker compose -f stack/domotica-voz/docker-compose.yml up -d`.
2. Configurar Home Assistant (solo la primera vez): `uv run stack/domotica-voz/setup/setup_ha.py`.
   Devuelve `OK: ...` o `<CÓDIGO>: qué hacer`. El token queda en `~/.agents/secrets/project_studio/ha.json`
   (fuera del repo; un agente delegado no lo lee).
3. Abrir el Estudio: `iniciar_estudio.bat` (Windows) o `iniciar_estudio.sh`.

## Mapa del código
| Zona | Archivos |
|---|---|
| Stack de voz (Docker) | `stack/domotica-voz/docker-compose.yml`, `mosquitto/mosquitto.conf`, `.env.example` |
| Configuración automática de Home Assistant | `stack/domotica-voz/setup/{setup_ha,flows,agents,ha_client}.py` |
| IAs disponibles (local y nube) | `stack/domotica-voz/ai_providers.json` (añadir una = añadir una entrada); claves en `~/.agents/secrets/project_studio/ai_keys.json` |
| Servidor del Estudio | `serve.py` (página, `/config.json`, audio), `serve_ai.py` (lista de IAs y guardar clave) |
| Tutorial 3D (copia del original) | `web/tutorials/circuito_3d/index.html` |
| Motor de bloques | `web/engines/blocks/` |
| Demo de voz (capas) | `web/demos/voice/js/{domain,application,infrastructure,presentation}/` |
| Pruebas | `tests/`: `node --test tests/*/*.test.mjs`; `uv run --no-project --with pytest pytest tests/server -q`; e2e en `tests/e2e/` |

## Códigos de error de setup_ha.py
`E_HA_DOWN`, `E_HA_HTTP`, `E_HA_AUTH`, `E_HA_WS`, `E_HA_ONBOARDED`, `E_FLOW_STEP`, `E_FLOW_ABORT`,
`E_AGENT`, `E_FLOW_INVALID` (clave rechazada), `E_ENTITY_MISSING`. Una IA de la nube que falla escribe
`AVISO <id> <CÓDIGO>: ...` y no detiene el resto. `serve_ai.py` añade `E_PROVIDER`, `E_KEY_FORMAT`, `E_SETUP`.

## Reglas del proyecto
- Código en inglés; textos de interfaz en `web/locales/es.json`.
- Puertos solo en 127.0.0.1. Ninguna marca, tienda ni precio en el repo: van en `../project_studio_data/`.
