# Cómo presentar el Estudio (unos 8 minutos)

## Antes de empezar
1. Doble clic en `iniciar_estudio.bat`. Se abre el Estudio en el navegador.
2. Haz una pregunta de calentamiento en la pestaña Demo (por ejemplo «¿qué hora es?»): la primera respuesta de la
   IA tarda más.

## Opción 1: se presenta solo
Pulsa **▶ Presentación**. El Estudio recorre las pantallas, habla con la voz local y hace las acciones de verdad:
cambia una pieza, avisa qué se rompe, la restablece y le pide a la demo que encienda el foco.
Controles: ⏸ pausa, ⏮ ⏭ escena, 🔊 voz, velocidad y ✕ (o Escape) para salir.
Si tu jefe pregunta algo, pausa y háblale al asistente en la pestaña Demo.

## Opción 2: lo presentas tú
1. **Inicio:** tres proyectos, todos con piezas abiertas.
2. **Demo:** «enciende el foco». Todo corre en la laptop, sin internet.
3. **Arquitectura:** toca «Centro de control» y elige openHAB. Sale el aviso: la voz necesita otra pieza.
   «Restablecer» vuelve a Home Assistant.
4. **Videoportero e industrial:** otros sectores con las mismas piezas.
5. **Flujo y Compras:** la lista para comprar de una vez y las tareas de cada etapa.
6. **Licencias:** qué se puede vender y qué documentos se entregan (botones de descarga).
7. **Cierre:** sin cuotas por cliente; siguiente paso, el prototipo real.

## El guion
La presentación es `web/studio/presentations/jefe.json`. Cada escena dice la pantalla, el texto, qué se resalta y
qué se hace. Se puede copiar y cambiar para cada cliente sin tocar el código.
