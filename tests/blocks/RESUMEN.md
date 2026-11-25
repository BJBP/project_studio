# Motor de bloques — resumen de la tarea

## Archivos creados

- `web/engines/blocks/layout.js` — estado de disposición puro, sin DOM. Exporta
  `defaultLayout`, `moveBlock`, `hideBlock`, `showBlock`, `setOption`,
  `mergeWithDefaults` y `LAYOUT_VERSION`. Ninguna función muta: todas devuelven
  un layout nuevo (copia profunda vía JSON).
  - `setOption` valida tipo y `min`/`max` (number), opciones de `select`
    (acepta choices como `"valor"` o `{ value, label }`) y devuelve
    `{ error: "E_OPTION_INVALID" }` si algo no cuadra.
  - `mergeWithDefaults`: versión distinta → layout por defecto; bloques nuevos
    se añaden según su `defaultVisible`; bloques que ya no existen se quitan de
    columnas, ocultos y opciones; las opciones guardadas que ya no validan
    caen a su valor por defecto.
  - `moveBlock` con un bloque desconocido es un no-op (no lo añade al layout).
- `web/engines/blocks/storage.js` — `createStorage(key)` sobre `localStorage`
  con try/catch. Si falla, `load()` devuelve `null` y escribe `console.warn`
  con el motivo; `save()` devuelve `false` y también avisa. Sin `catch` vacío.
- `web/engines/blocks/block-manager.js` — `mountBlocks(root, { blocks, columns, storage, t })`.
  Columnas con cabecera opcional, bloque con asa de arrastre (⠿, HTML5 drag & drop),
  título, botón ⚙ (formulario de opciones generado desde `optionsSchema`:
  checkbox / number con min-max / select / text) y botón ✕ (ocultar).
  Con teclado: el asa enfocada mueve el bloque con las flechas (↑↓ dentro de la
  columna, ←→ entre columnas) y conserva el foco. Barra superior con
  «+ Añadir bloque» (menú de ocultos) y «⟲ Restablecer» (con `confirm`).
  Cada cambio guarda el layout y re-renderiza solo el bloque afectado
  (los movimientos entre columnas recolocan el elemento sin re-renderizar).
  Devuelve `{ destroy() }`: aborta listeners (AbortController) y llama a
  `destroy` de cada bloque montado. Sin `innerHTML`: todo se crea con
  `createElement`/`textContent`. Los textos visibles salen del objeto `t`
  (con valor alternativo en código si falta una clave).
- `web/engines/blocks/blocks.css` — variables CSS en `:root`, modo oscuro con
  `@media (prefers-color-scheme: dark)`, columnas en CSS grid que pasan a una
  sola columna por debajo de 720 px, indicador de destino de arrastre.
- `web/engines/blocks/demo.html` — página de ejemplo con 3 bloques (boolean,
  number, select) y objetos `t` en español. Para probar a mano en el navegador.
- `tests/blocks/layout.test.mjs` — pruebas con `node:test`.

## Salida de las pruebas

Comando pedido en la tarea (`node --test tests/blocks/`): **falla en este equipo**
con Node v22.23.2 — el runner ya no acepta un directorio como argumento posicional
y lo trata como un módulo que no existe:

```
# Error: Cannot find module 'C:\ruta\a\project_studio\tests\blocks'
#   code: 'MODULE_NOT_FOUND'
```

La misma suite pasa con el glob o con el archivo concreto:

```
$ node --test "tests/blocks/*.test.mjs"
1..12
# tests 12
# pass 12
# fail 0
# duration_ms 93.9218
```

(`node --test tests/blocks/layout.test.mjs` da la misma salida: 12/12 pass.)

Cobertura: defaultLayout, no-mutación, moveBlock entre columnas y reordenado,
clamp de índice, hideBlock, showBlock, setOption válida / fuera de rango / tipo
incorrecto / clave desconocida, merge con bloque nuevo, merge con bloque
eliminado, opciones guardadas inválidas y versión distinta.

## Verificación de la demo

El navegador disponible para automatización (Playwright) bloquea tanto
`http://127.0.0.1:<puerto>` como `file://` (`ERR_BLOCKED_BY_CLIENT` / acceso
a `file:` bloqueado), así que la demo queda **sin probar en navegador**; el
servidor estático de prueba se arrancó y se paró después. Comprobado solo por
importación del módulo en Node (`import('.../block-manager.js')` → OK).
Abrir `web/engines/blocks/demo.html` en un navegador para probarla a mano:
arrastrar bloques, cambiar opciones, ocultar, «+ Añadir bloque» y «⟲ Restablecer».

## Pendientes / notas

- Probar la demo en un navegador real (arrastre, formularios, foco de teclado).
- `node --test tests/blocks/` tal como está en la tarea no funciona en
  Node ≥ 21; usar el glob o el archivo concreto.
