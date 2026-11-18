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
| Configuración automática de Home Assistant | `stack/domotica-voz/setup/{setup_ha,flows,ha_client}.py` |
| Tutorial 3D (copia del original) | `web/tutorials/circuito_3d/index.html` |
| Motor de bloques | `web/engines/blocks/` |
| Demo de voz (capas) | `web/demos/voice/js/{domain,application,infrastructure,presentation}/` |
| Pruebas | `tests/` |

## Códigos de error de setup_ha.py
`E_HA_DOWN`, `E_HA_HTTP`, `E_HA_AUTH`, `E_HA_WS`, `E_HA_ONBOARDED`, `E_FLOW_STEP`, `E_FLOW_ABORT`,
`E_OLLAMA_AGENT`, `E_ENTITY_MISSING`.

## Reglas del proyecto
- Código en inglés; textos de interfaz en `web/locales/es.json`.
- Puertos solo en 127.0.0.1. Ninguna marca, tienda ni precio en el repo: van en `../project_studio_data/`.
