# Activar por voz y elegir el modelo de IA

## Decisiones aprobadas (2026-11-18)
- La demo del navegador se activa diciendo «okay nabu», igual que el ESP32 real. No hace falta botón.
- El detector de la palabra es microWakeWord (Apache 2.0) en Docker (`rhasspy/wyoming-microwakeword`).
  Se descarta openWakeWord: sus modelos entrenados son de uso no comercial (CC BY-NC-SA).
- El bloque «Cerebro» elige también el modelo. Los modelos locales salen de los instalados en Ollama; los de la nube,
  de la lista de cada proveedor en `ai_providers.json`.

## Mockup
```
┌ 🎙️ Hablar ─────────────────── ⚙ ✕ ┐     ┌ 🧠 Cerebro ─────────────────── ⚙ ✕ ┐
│ IA: Local (Ollama)                 │     │ IA:     [ Local (Ollama)      ▾ ]  │
│ [● Activar por voz]                │     │ Modelo: [ qwen3.5:4b          ▾ ]  │
│ 👂 Esperando «okay nabu»…          │     │ ℹ 4 GB de GPU: los modelos de más  │
│ 🔴 Te escucho…                     │     │   de ~4 GB van lentos.             │
│ ⚠ Micrófono sin permiso            │     │ ✅ Usando qwen3.5:4b               │
│ [ Mantén para hablar ]             │     │ ⚠ El modelo no responde: se vuelve │
└────────────────────────────────────┘     │   al anterior                      │
                                           └────────────────────────────────────┘
```

## Ejemplos de uso
- «Okay nabu… enciende el foco» → foco encendido y OLED «FOCO:ON».
- Hablar sin decir «okay nabu» → no pasa nada.
- Cambiar a `qwen3:1.7b` → la siguiente respuesta llega antes, con menos precisión.

## Piezas
| Capa | Archivo |
|---|---|
| Stack | `stack/domotica-voz/docker-compose.yml` (servicio `wakeword`) |
| Configuración | `setup/flows.py` (integración y palabra en cada asistente) |
| Servidor | `serve_ai.py` (lista de modelos y cambio de modelo) |
| Navegador | `infrastructure/ha-assist.js` (inicio en la palabra), `application/assistant-session.js` (modo manos libres), bloques `talk-block.js` y `brain-block.js` |

## Verificación
Pruebas de Node con un Home Assistant falso; en el navegador, «okay nabu, enciende el foco» con voz de Piper
inyectada en el micrófono; cambio de modelo y respuesta escrita.

## Estado
En curso.
