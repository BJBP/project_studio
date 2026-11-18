# IA intercambiable (local o nube)

**Estado: hecho el 2026-11-18** (antes de la fase 2). Falta probar con una clave real: ver `docs/backlog.md`.

## Decisión aprobada
La IA es una pieza intercambiable. Por defecto se usa la local (Ollama). El cliente puede añadir una IA en la nube
(Claude, OpenAI, Gemini) con su clave. Las órdenes simples («enciende el foco») las resuelve Home Assistant sin IA,
así que la casa funciona aunque no haya internet.

## Mockup
```
┌ Cerebro (IA) ─────────────────── ⚙ ✕ ┐
│ Local (Ollama)               En uso  │
│ Sin internet · gratis · privado      │
│ Claude              [Añadir clave]   │
│ En la nube · de pago · ⚠ datos salen │
│   Clave de Claude [••••••••]         │
│   [Guardar]  Cómo conseguir la clave │
│   (error: «La clave no funciona…»)   │
│ OpenAI / Gemini     [Añadir clave]   │
└──────────────────────────────────────┘
Hablar: «IA: Local (Ollama)» encima del botón.
Si la IA de la nube falla: aviso y la siguiente orden va a la local.
```

## Ejemplos de uso
- Con clics: bloque «Cerebro» → «Añadir clave» → pegar → «Guardar» → «Usar».
- Agente: guardar `{"claude": "<clave>"}` en `~/.agents/secrets/project_studio/ai_keys.json` y ejecutar
  `uv run stack/domotica-voz/setup/setup_ha.py` (imprime `AVISO <id> ...` si una clave falla).
- Añadir otra IA: una entrada en `stack/domotica-voz/ai_providers.json` con la integración de Home Assistant.

## Cómo funciona (capas)
- Datos: `ai_providers.json` (repo, sin claves) y `ai_keys.json` (fuera del repo).
- Configuración: `setup/agents.py` crea en Home Assistant un asistente por IA con clave («Asistente Claude»…).
- Servidor: `serve_ai.py` da la lista a la página y guarda la clave; si Home Assistant la rechaza, no se guarda.
  Solo acepta peticiones de la propia página (127.0.0.1, mismo origen).
- Dominio: `brains.js` (estado de cada IA y cuál usar). Aplicación: `brain-choice.js`. Presentación: `brain-block.js`.

## Escala y riesgos
- Cualquier integración de conversación de Home Assistant entra sin tocar código.
- Privacidad: con una IA en la nube, lo que se dice sale del equipo; el bloque lo avisa.
- Coste: las IAs de la nube cobran por uso a la cuenta de la clave.

## Verificación
- 66 pruebas de Node y 4 de Python. Navegador: el bloque lista las IAs, una clave falsa muestra el error y no se
  guarda, y la IA local responde con su asistente.
