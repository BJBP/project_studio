# Plan: conexiones externas

Estado: fase 1 hecha (2026-11-20).

## Para qué
Los aparatos de Home Assistant se comparten con otras plataformas (una central de monitoreo, un panel de empresa…).
Cada plataforma es una **conexión**. Cada tipo de plataforma es un **conector**: una carpeta en `connectors/` del programa
o en `<datos>/connectors/` (los privados, cada uno en su propio repositorio con su instalador).
El Estudio trae el administrador; el repositorio no lleva direcciones ni nombres de ninguna plataforma concreta.

## Decisiones aprobadas
- Un administrador «Conexiones externas» (módulo `conexiones`, bloque en la pestaña Aparatos).
- Conector = carpeta con `connector.json` (nombre, licencia, opciones en esquema) y `translate.py` (traducción pura).
- Conexiones en `<datos>/connections.json`; estado en vivo en `<datos>/connections_status.json`.
- Un proceso de fondo (`connectors/run.py`, lanzado por el Estudio) escucha Home Assistant y publica; ejecuta en
  Home Assistant las órdenes que llegan. Un solo proceso a la vez (archivo de bloqueo con latido).
- El primer conector (MQTT, telemetría numérica y órdenes encender/apagar/alternar) vive en un repositorio privado.
- Cada aparato acepta órdenes de una sola conexión (`direction: both`); las demás solo envían (`send`).

## Mockup
```
┌ Conexiones externas ─────────────── [+ Añadir] ┐
│ 📡 Central       MQTT          ✓ Conectada  ⚙│
│    1 aparato · último cambio hace 3 s          │
└────────────────────────────────────────────────┘
⚙ Central
  Nombre [Central]  Tipo [MQTT]
  Servidor [127.0.0.1] Puerto [1885] Prefijo [devices]
  Aparatos que comparte:
   [✓] Foco (placa)   → placa-foco    ⇄ envía y recibe
   [ ] Cooler         → placa-cooler  → solo envía
  [Guardar] [Pausar] [Eliminar]
 Vacío: «Aún no hay conexiones. Pulsa + Añadir.»
 Error: ⚠ No responde 127.0.0.1:1885 → enciende la plataforma.
```

## Ejemplos
- Enciendes el foco por voz → la plataforma recibe `{"state": 1}` para `placa-foco`.
- La plataforma manda «apagar» a `placa-foco` → Home Assistant apaga el foco.

## Capas
- dominio: `studio/domain/connections.py` (validación, códigos `E_CONN_*`).
- aplicación: `studio/application/connections.py` (puerto `ConnectionStore`, casos de uso).
- infraestructura: `studio/infrastructure/connection_store.py` (JSON), `connectors/*` (conectores y proceso).
- presentación: rutas `/api/studio/connections`, `serve_connections.py`, bloque `connections-block.js`.

## Fases
1. Administrador, primer conector, foco de la placa; prueba de punta a punta. ← hecha
2. Enchufe S40 cuando esté en Home Assistant.
3. Más conectores (MQTT genérico, webhook HTTP).

## Hasta dónde escala
Cientos de aparatos por conexión y decenas de conexiones en un proceso. Lo primero que se satura es la lista de
aparatos en la pantalla (hará falta buscador) y, con miles de cambios por segundo, un proceso por conexión.

## Verificación
Pruebas de dominio y bloque (con un conector de prueba neutro). En vivo: la plataforma recibió `{"state": 1}` y
`{"state": 0}` y sus órdenes encendieron y apagaron el foco real.
