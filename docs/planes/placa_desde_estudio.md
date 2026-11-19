# Placa real desde el Estudio (instalar y Wi-Fi sin navegador especial)

## Estado
Hecho (2026-11-19). Probado con la placa real: instalar por COM4, ver su IP y añadirla a Home Assistant.
Falta probar «Conectar» con una red nueva (la placa ya tenía Wi-Fi).

## Decisión
El Estudio pide el Wi-Fi en su propia pantalla y lo guarda en la carpeta de secretos (fuera del repo). Las mismas
piezas sirven a un agente por la línea de órdenes; la contraseña va por la entrada estándar y no se imprime.
El firmware escucha Improv en el conector «COM» (`logger: hardware_uart: UART0`) y devuelve su IP (`next_url`).

## Mockup (Aparatos → tarjeta de la placa)
```
Puerto: [COM4 · conector COM (CH34x) ▾] [↻]
[⚡ Instalar firmware] [📶 Ver la placa y sus redes]
[🏠 Añadir a Home Assistant]        ← solo si ya tiene Wi-Fi
┌ Wi-Fi de la placa ──────────────────────────┐
│ Red:        [MiRed        ] (lista + escribir)│
│ Contraseña: [••••••] 👁                        │
│ ☑ Recordar en este equipo (no sale de aquí)   │
│ [Conectar]                                    │
└───────────────────────────────────────────────┘
✅ Placa en 192.168.8.65 y añadida a Home Assistant.
⚠ COM4 ocupado: cierra el otro programa.
```

## Ejemplos
- Clics: Aparatos → ⚡ Instalar firmware → (al terminar) elegir red, contraseña → Conectar.
- Agente: `uv run firmware/board.py flash circuito_maestro --port COM4`, luego `status --port COM4` → IP, y
  `uv run stack/domotica-voz/setup/esphome_device.py <IP>`.

## Archivos
`firmware/{board,improv,improv_link}.py`, `serve_board.py`, `serve_jobs.py`, `web/studio/js/blocks/board-panel.js`,
`firmware/esphome/packages/wifi.yaml`; pruebas en `tests/firmware/test_improv.py`, `tests/server/test_serve_board.py`.
