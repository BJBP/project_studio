# Plan: administrador de la pantalla de la placa y pantalla virtual

Estado: propuesto (2026-11-20), pendiente de aprobar. Nada construido.

## Para qué
Hoy lo que muestra la pantalla OLED (128×64) está fijo en `firmware/esphome/packages/oled.yaml`: «FOCO/FAN», el
texto «Pantalla» que escriben la voz y las automatizaciones, y «Sin motor». Cambiarlo obliga a compilar e instalar el
firmware. El administrador decide qué va en la pantalla desde el Estudio, y una página web muestra lo mismo.

## Decisiones propuestas (pendientes)
- Un solo diseño (JSON en la carpeta de datos) para dos salidas: la pantalla de la placa y la página
  «Pantalla virtual».
- El firmware dibuja N líneas que Home Assistant escribe; N y las letras por línea salen de la pantalla y la letra de
  cada placa. Se instala una vez; después todo se cambia desde el Estudio.
- Sin Home Assistant, la placa muestra lo de hoy (estado del relé y «Sin motor»).
- Tipos de línea: estado de un aparato, valor de un sensor, mensajes de voz, hora, Wi-Fi o IP, texto fijo, vacía.
- Estados de voz en las dos salidas: en reposo (imagen y hora), «Escuchando…» con nivel del micrófono, lo que
  entendió, la respuesta (3 s) y vuelta al reposo.
- Imagen: se sube en el bloque; en la placa se convierte a 1 bit y va dentro del firmware (cambiarla = reinstalar);
  en la página se ve en color.
- Aprovechar la misma instalación para arreglar el micrófono que se apaga solo (ver `docs/backlog.md`).

## Mockup
```
┌ 🖥 Pantalla de la placa ──────────────── ⚙ ┐
│ Vista previa         Líneas               │
│ ┌──────────────┐  1 [Estado ▾] Ventilador ⠿│
│ │FOCO: ON      │  2 [Mensajes de voz ▾]   ⠿│
│ │Listo. Di una │  3 [Hora ▾]              ⠿│
│ │12:45         │  4 [Sensor ▾] Temperatura⠿│
│ │T: 21.5 °C    │  5 [Vacía ▾]             ⠿│
│ └──────────────┘                [Restablecer]│
│ Imagen: [🖼 Subir]   [Guardar en la placa] │
└────────────────────────────────────────────┘
 Sin placa:  «La placa no está conectada; se guarda y se envía al volver.»
 Error:      ⚠ Línea 4: «sensor.temp» no existe (E_OLED_ENTITY)
 Firmware viejo: «Esta placa necesita el firmware nuevo una vez. [Instalar]»

Página «Pantalla virtual» (/studio/pantalla)
┌──────────────────────────┐   ┌──────────────────────────┐   ┌──────────────────────────┐
│ [🖼 imagen]      12:45   │ → │ 🎙  Escuchando…   ▂▄▆▄▂  │ → │ 💬 Apagado el foco       │
│   Listo. Di una orden    │   │ «apaga el foco»          │   │                          │
│ FOCO: ON                 │   │                          │   │                          │
└──────────────────────────┘   └──────────────────────────┘   └──────────────────────────┘
 Sin conexión: «Sin conexión con Home Assistant · reintentando»
```

## Ejemplos de uso
- Línea 4 → Sensor → Temperatura → Guardar: «T: 21.5 °C» aparece en la placa y en la página.
- Abrir `/studio/pantalla` en el celular a pantalla completa; al decir «Okay Nabu» pasa a «Escuchando…».
- Restablecer vuelve al diseño de hoy.

## Fases
1. Diseño compartido, página «Pantalla virtual», firmware con líneas, imagen y estados de voz (más el arreglo del
   micrófono) y bloque de edición con vista previa; orden `python -m studio oled …` para agentes.
2. Varias páginas que se pasan solas o con el botón de la placa.
3. Iconos y letra más grande.

## Capas
- dominio: diseño de pantalla (validar líneas, tipos, longitudes según la pantalla).
- aplicación: guardar y leer el diseño, calcular el texto de cada línea.
- infraestructura: JSON en datos, escritura en Home Assistant, conversión de la imagen.
- presentación: bloque del Estudio, página `/studio/pantalla`, firmware `oled.yaml`.

## Reutilizar
`web/studio/js/ha-live.js` (estados en vivo), `voice-monitor-block.js` y `voice-runs.js` (paso del asistente y nivel
del micrófono), sensor `sound_level` de `packages/voice.yaml`.

## Verificación
Pruebas del diseño (líneas largas, entidad que no existe, tipos). En el navegador: cambiar una línea y verla en la
página; decir «Okay Nabu» y ver «Escuchando…» en la página y en la placa real.
