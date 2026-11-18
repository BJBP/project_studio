# Backlog

- Probar la voz real con el micrófono del navegador (solo se probó la orden escrita en la página y la voz con `tests/e2e/voice_pipeline.py`).
- El indicador «Micrófono» dice «Sin conexión» hasta la primera vez que se pulsa «Mantén para hablar»: mejor «Sin usar».
- Probar `iniciar_estudio.bat` de principio a fin en una máquina limpia.
- Antes de una demo, hacer una pregunta de calentamiento: la GPU de 4 GB va justa y la primera respuesta de la IA puede fallar.
- `web/demos/voice/js/infrastructure/ha-assist.js` tiene 176 líneas: separar `request()` (peticiones sueltas) de las ejecuciones de voz.
- `tests/e2e/device_control.py` necesita la página Demo abierta una vez (anuncia los aparatos): automatizarlo sin navegador.

- Mosquitto sin usuario ni clave (solo 127.0.0.1): añadir usuarios antes de usarlo en una red de cliente.
- Ollama escucha en 0.0.0.0 en esta laptop (ajuste previo del equipo): visible en la red local.
- Revisar la licencia de la voz de Piper `es_ES-davefx-medium` y de `qwen3.5:4b` antes de ofrecerlo a clientes.
- IA en la nube: probada solo con una clave falsa (se rechaza y no se guarda). Falta probar Claude, OpenAI y Gemini con una clave real.
- IA en la nube: botón para quitar una clave (hoy hay que borrarla de `ai_keys.json` y de Home Assistant).
- IA en la nube: elegir sola la IA según la pregunta (local para lo simple, nube para lo difícil). Home Assistant no lo trae hecho.
- Si la IA de la nube falla con una orden de voz, la orden no se repite con la local: solo la siguiente usa la local.
- Fases 2–5 del plan.
- `web/engines/blocks/block-manager.js` tiene 500 líneas: dividir en cabecera de bloque, formulario de opciones, arrastrar/teclado y barra.
- Probar el motor de bloques en modo claro y en pantalla de móvil.
