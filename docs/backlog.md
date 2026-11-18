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
- Compras: buscar 2–3 mini PC candidatas y completar precios en `project_studio_data/catalog/models.json` (no se inventan).
- Presentación: exportarla como video.
- El diagrama ocupa poco en pantallas estrechas: probar en móvil y, si hace falta, hacer zoom y desplazamiento.
- Recorrido de la Ayuda: probado solo el motor (la Presentación); revisar sus escenas una a una.
- Cámara: probada solo la lógica de movimiento (pruebas de Node); falta probarla con la cámara USB real y su permiso.
- Modos Intercomunicador y Acústico: comprobados solo por sus reglas; probarlos en el navegador como Seguridad y Salud.
- Demo de voz: mientras conecta con Home Assistant la página queda en blanco unos segundos; mostrar «Conectando…».
- Reorganizaciones propuestas por el análisis de la fase 1 (`.git/analisis_fase1.md`, por decidir): helper común de
  suscripción para bloques (2–3 h), dividir block-manager.js (4–6 h), puerto `ha-gateway` (3–5 h), helpers de
  interruptor (1–2 h), lectura común de ai_providers/ai_keys (1–2 h), dividir ha-assist.js (3–4 h).
- Fase 4: flashear el ESP32 real desde «Aparatos» (necesita el cable USB) y probar Wi-Fi por Improv, OTA y la voz «okay nabu».
- Fase 4: el cooler necesita el segundo relé (`packages/relay2.yaml`) cableado; el firmware aún no envía el nivel de sonido del micrófono (dB).
- Fase 4: el panel de ESPHome guarda su estado (`.device-builder*`) dentro de `firmware/esphome/`; está ignorado por git, pero mejor montarlo en la carpeta de datos.
- Fase 5: revisar los nombres de columna de `inventree_partes.csv` y `odoo_productos.csv` importándolos en una instancia real.
- Fase 5: modos de videoportero e industrial probados de uno en uno («Portero», «Sobretemperatura»); faltan «Visita detectada» y «Vibración alta» en el navegador.
- Fase 4: la primera compilación tarda más de 1 h porque `.esphome/` (ESP-IDF y la compilación) está en una carpeta de Windows montada en Docker; usar un volumen de Docker para `.esphome/`.
- Fase 4b (mini PC): paquete de instalación para Linux y copias de seguridad, cuando se compre.
- `web/engines/blocks/block-manager.js` tiene 500 líneas: dividir en cabecera de bloque, formulario de opciones, arrastrar/teclado y barra.
- Probar el motor de bloques en modo claro y en pantalla de móvil.
- Activar por voz: probar con un micrófono real en Chrome o Edge (el panel de la app bloquea el micrófono; se probó con la voz de Piper como micrófono).
- Activar por voz: Piper en español no siempre dice bien «Okay Nabu» (con «Okey Nabu» sí); revisar con personas reales y ruido de fondo, y la sensibilidad.
- Elegir modelo: el cambio ejecuta todo `setup_ha.py` (unos segundos); un comando solo para el modelo lo haría más rápido.
- Elegir modelo en la nube: sin probar con una clave real; añadir la lista de modelos de OpenAI y Gemini en `ai_providers.json`, o pedirla al proveedor.
- Docker del Estudio: probar guardar una clave o cambiar de modelo desde el contenedor (ejecuta `setup_ha.py` con uv dentro).
