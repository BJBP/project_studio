# Modo cable: la placa en Home Assistant por el cable USB

Estado: **hecho** (2026-11-19). Pendiente: la prueba con la persona usuaria quitando el Wi-Fi, desde la pantalla.

## Decisiones aprobadas
- La placa habla por el conector «COM» con líneas de texto que empiezan por «@» (componente `serial_bridge` del
  firmware). Sustituye a Improv: el Wi-Fi también se envía por estas líneas.
- El Estudio tiene un **puente** (`firmware/cable_bridge.py`). Mientras la placa no tiene Wi-Fi, el puente la anuncia
  en Home Assistant como «Circuito maestro (cable)», con los nombres elegidos en «Qué hay conectado», y le pasa las
  órdenes. Cuando vuelve el Wi-Fi, el puente quita ese aparato y manda la placa por Wi-Fi.
- Mientras va por cable, el asistente de voz solo ve las entidades del cable. Así «apaga el ventilador» llega a la
  placa. Al volver el Wi-Fi, ve otra vez las de Wi-Fi.
- Por el cable no hay voz: el micrófono y el altavoz de la placa necesitan Wi-Fi. La orden escrita o la voz del
  navegador sí funcionan.
- La búsqueda de redes desde la placa desaparece: la red se escribe (solo de 2,4 GHz).

## Mockup (bloque «Placa», en Aparatos)
```
┌ Placa ─────────────────────────────────────┐
│ Puerto [COM4 · conector COM (CH34x) ▾] [↻] │
│ [⚡ Instalar firmware] [📶 Ver cómo está…] │
│ ☑ 🔌 Por cable: sin Wi-Fi, la placa sigue  │
│   en Home Assistant por este cable (sin voz)│
│   la placa sigue en Home Assistant por el   │  ← estado del puente (verde)
│   cable                                     │
│ ┌ Wi-Fi de la placa ─────────────────────┐ │
│ │ Red [________]  Contraseña [____] [👁] │ │
│ │ ☑ Recordar en este equipo  [Conectar]  │ │
│ └────────────────────────────────────────┘ │
└────────────────────────────────────────────┘
Gemelo digital:  ● En línea por Wi-Fi | ● En línea por cable | ⚠ Placa sin conexión
Error:           ⚠ E_PORT_LOST: se perdió la placa (¿cable suelto?)…
```

## Ejemplos de uso
- Con clics: Aparatos → Placa → marcar «🔌 Por cable». El gemelo digital dice «En línea por cable» y un clic en el
  relé lo enciende.
- Línea de comandos: `uv run firmware/cable_bridge.py --port COM4` (queda en marcha; Ctrl+C para salir) y después
  `uv run firmware/cable_bridge.py --restore`.
- Estado de la placa: `uv run firmware/board.py status --port COM4` → `{"online": false, "ip": null}`.

## Capas y archivos
- Firmware: `firmware/esphome/components/serial_bridge/`, `packages/wifi.yaml`.
- Reglas puras (líneas y mensajes MQTT): `firmware/cable.py`. Pruebas: `tests/firmware/test_cable.py`.
- Puerto serie: `firmware/board_link.py`, `firmware/board.py`. Puente: `firmware/cable_bridge.py`.
- Servidor: `serve_board.py` (`start_cable`, `stop_cable`, `cable_status`; las demás acciones pausan el puente),
  `serve_jobs.py` (tareas que se pueden parar), rutas en `serve.py` (`/api/board/cable`, `/api/board/status`).
- Pantalla: `web/studio/js/blocks/board-panel.js`, `web/studio/js/twin-sync.js` (`realLink`), `twin-block.js`.

## Hasta dónde escala
Un puente por placa y por puerto. Con varias placas, cada una lleva su propio puente (la clave es el puerto) y su
`--device`. Lo primero que se rompe: el catálogo da un solo aparato por puerto y la búsqueda por nombre asume nombres
únicos dentro de una placa.

## Verificación
- Pruebas sin placa: `pytest tests/firmware tests/server`, `node --test tests/*/*.test.mjs`.
- Con la placa: el firmware compiló e instaló; `status` responde por el cable; Home Assistant encendió el relé por
  el cable y recibió su estado.
