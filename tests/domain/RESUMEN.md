# Resumen: capa de dominio de la demo de voz

## Archivos creados

Módulos (`web/demos/voice/js/domain/`):

- `catalog.js` — `validateCatalog(data)` con los códigos `E_NO_DEVICES`, `E_DEVICE_ID`,
  `E_DUPLICATE_ID`, `E_ENTITY_KEY`, `E_COMPONENT`, `E_NAME`.
- `topics.js` — `stateTopic`, `commandTopic`, `availabilityTopic`.
- `discovery.js` — `buildDiscovery(catalog)`: un mensaje retained por entidad, con el
  payload común y los campos por componente (switch, button, text, sensor).
- `device-state.js` — `initialState`, `parseCommandTopic`, `applyCommand` (sin mutar el
  estado; eventos `changed`, `pressed`, `error` con `E_BAD_PAYLOAD` / `E_UNKNOWN_ENTITY`).
- `oled.js` — `oledLayout({ header, body })`: header de máx. 21 caracteres, cuerpo
  envuelto por palabras en máx. 6 líneas de 21, palabras largas cortadas y última línea
  con «…» si sobra texto.
- `audio-level.js` — `rmsToDb(samples)`: dB redondeados a entero, mínimo −90.

Pruebas (`tests/domain/`): `catalog.test.mjs`, `topics.test.mjs`, `discovery.test.mjs`,
`device-state.test.mjs`, `oled.test.mjs`, `audio-level.test.mjs` (node:test +
node:assert/strict; 23 casos, con errores en los módulos que los tienen).

## Nota sobre el comando de pruebas

`node --test tests/domain/` falla en este equipo (Node v22.23.2 en Windows): trata la
carpeta como un módulo y lanza `Cannot find module ...\tests\domain`. La forma con
comodín funciona y es la que se ejecutó:

`node --test tests/domain/*.test.mjs`

## Salida final

```
1..23
# tests 23
# suites 0
# pass 23
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 164.2421
```

Ningún archivo fuera de `web/demos/voice/js/domain/` y `tests/domain/` fue modificado.
No se hizo commit.
