# Backlog

- Probar la voz real con el micrófono del navegador (solo se probó la orden escrita en la página y la voz con `tests/e2e/voice_pipeline.py`).
- El indicador «Micrófono» dice «Sin conexión» hasta la primera vez que se pulsa «Mantén para hablar»: mejor «Sin usar».
- Probar `iniciar_estudio.bat` de principio a fin en una máquina limpia.
- La orden de pruebas de `tests/server` del `AGENTS.md` falla al cargar 2 archivos (falta `httpx`): añadir `--with httpx --with websockets`.
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
- Placa real: instalada desde el Estudio y en Home Assistant (2026-11-19); relé, pantalla y zumbador comprobados en la placa. Falta probar «Conectar» con una red nueva (la placa ya tenía Wi-Fi), OTA y la voz «okay nabu».
- Monitor de voz: lee `get_states` cada segundo y el historial de órdenes de todo el asistente (también las de la Demo); con muchos aparatos, cambiar a `subscribe_entities`. Importa `ha-assist.js` de la Demo: moverlo a `web/shared/`.
- Gemelo digital: el clic en el 3D a veces cae en un cable que pasa por encima del relé; dar prioridad a las piezas sobre los cables. La pantalla OLED del 3D aún no se puede editar con un clic.
- Gemelo digital: hoy solo para el Circuito maestro (las piezas del 3D están fijas en el tutorial); para otros aparatos, generar el 3D desde el catálogo de piezas.
- «Qué hay conectado»: probar que la voz usa el nombre nuevo («apaga el ventilador») con la placa real.
- Modo cable: probado por línea de comandos con la placa (relé y orden escrita). Falta probarlo desde la pantalla, quitando el Wi-Fi.
- Modo cable: si el Estudio se cierra con el puente en marcha, el asistente sigue sin ver las entidades de Wi-Fi hasta el próximo puente o `cable_bridge.py --restore`.
- Modo cable: «⚡ Instalar por USB» del navegador ya no pide el Wi-Fi (sin Improv); el Wi-Fi se escribe en el bloque Placa.
- Modo cable: la placa no busca redes; se podría añadir «@scan» al firmware para llenar la lista.
- Placa por USB desde el Estudio en Docker: el contenedor no ve el puerto COM en Windows; la pantalla lo avisa y queda «⚡ Instalar por USB».
- Fase 4: el cooler necesita el segundo relé (`packages/relay2.yaml`) cableado; el firmware aún no envía el nivel de sonido del micrófono (dB).
- Fase 4: el panel de ESPHome guarda su estado (`.device-builder*`) dentro de `firmware/esphome/`; está ignorado por git, pero mejor montarlo en la carpeta de datos.
- Fase 5: revisar los nombres de columna de `inventree_partes.csv` y `odoo_productos.csv` importándolos en una instancia real.
- Fase 5: modos de videoportero e industrial probados de uno en uno («Portero», «Sobretemperatura»); faltan «Visita detectada» y «Vibración alta» en el navegador.
- Fase 4: `build_firmware.py` ya compila en un volumen de Docker (unos 5 min); el panel de ESPHome (OTA) sigue usando la carpeta de Windows.
- Fase 4b (mini PC): paquete de instalación para Linux y copias de seguridad, cuando se compre.
- `web/engines/blocks/block-manager.js` tiene 500 líneas: dividir en cabecera de bloque, formulario de opciones, arrastrar/teclado y barra.
- Probar el motor de bloques en modo claro y en pantalla de móvil.
- Activar por voz: probar con un micrófono real en Chrome o Edge (el panel de la app bloquea el micrófono; se probó con la voz de Piper como micrófono).
- Activar por voz: Piper en español no siempre dice bien «Okay Nabu» (con «Okey Nabu» sí); revisar con personas reales y ruido de fondo, y la sensibilidad.
- Elegir modelo: el cambio ejecuta todo `setup_ha.py` (unos segundos); un comando solo para el modelo lo haría más rápido.
- Elegir modelo en la nube: sin probar con una clave real; añadir la lista de modelos de OpenAI y Gemini en `ai_providers.json`, o pedirla al proveedor.
- Docker del Estudio: probar guardar una clave o cambiar de modelo desde el contenedor (ejecuta `setup_ha.py` con uv dentro).
- Palabra propia, fase B: entrenar desde el Estudio (`docs/planes/palabra_propia.md`). Necesita ~40 GB libres (hoy 15 GB) y parar Ollama mientras entrena (GPU de 4 GB).
- Palabra propia: probar con un `.json` + `.tflite` de un entrenador real (se probó con un modelo de Okay Nabu renombrado).
- Palabra propia: borrar una palabra importada desde la página (hoy se borran sus dos archivos de `project_studio_data/wake_words/`).
- Palabra propia en Docker del Estudio: el contenedor no puede reiniciar el detector; avisa de reiniciar el stack de voz.
- La palabra del ESP32 real va en `firmware/esphome/packages/voice.yaml`: cambiarla desde el Estudio y volver a compilar.
- Simulador del ESP32 (pendiente): esperar a ESPHome, o probar la alternativa 1 (`external_components`, ~3 h) o la 2 (híbrida); detalle en el plan. Con cada versión nueva de ESPHome, probar `build_firmware.py circuito_maestro --sim` (`docs/planes/simulador_esp32.md`).

## Integrar en vez de programar (sugerencias)
- Primero, el sistema de módulos (integraciones y también tipos de proyecto, bloques, pantallas…): cada módulo en `modules/<id>/` con su manifiesto (licencia, servicio Docker,
  botones, bloques o pestañas, opciones) y un administrador «Módulos» en el Estudio para instalar, activar,
  desactivar y desinstalar con un clic. Las integraciones de abajo llegan como módulos. Plan hecho, pendiente por decisión del usuario:
  `docs/planes/sistema_modulos.md`.
- ESPConnect (MIT, ~2.2k estrellas, solo navegador, Docker en local): administrar la placa (copias de seguridad,
  monitor serie, particiones, archivos). Servicio en el stack y botón «🔧 Administrar placa» en Aparatos. Sustituye a
  copias y monitor propios. ~1 h.
- Home Assistant como administrador de aparatos y automatizaciones: enlaces desde el Estudio a sus páginas en vez de
  editores propios. ~1 h.
- Frigate (MIT) para el videoportero: detección de personas con la cámara real, en vez de ampliar la detección de
  movimiento propia. Necesita GPU o Coral; revisar en la mini PC.
- Node-RED (Apache 2.0) para flujos del proyecto industrial sin programar. n8n es «fair-code»: uso interno sí,
  revenderlo no.
- InvenTree (MIT) por su API en vez de solo exportar CSV: el inventario y las compras se actualizan solos.
- Zigbee2MQTT (GPL-3.0, se usa como programa aparte): aparatos Zigbee comerciales sin firmware propio.
