# Project Studio

Un estudio para armar y mostrar proyectos de **domótica, videoportero y monitoreo industrial** hechos solo con
**software abierto, protocolos abiertos e IA local**. Ejemplo: un asistente de voz tipo «Alexa» que funciona sin nube,
con una placa ESP32, Home Assistant y un modelo de IA en tu propio equipo.

En el Estudio cada proyecto muestra su arquitectura, se pueden cambiar sus piezas (con sus licencias y su
compatibilidad) y se ve funcionar: voz, aparatos reales y simulados, un gemelo digital en 3D, compras y documentos de
entrega.

## Qué trae
- **Proyectos de ejemplo**: domótica con voz local, videoportero e industrial (`examples/projects/`).
- **Voz local**: Home Assistant con reconocimiento de voz, síntesis (Piper), palabra para despertar e IA local
  (Ollama) o en la nube, a elección.
- **Placa ESP32 desde el navegador**: instalar el firmware por USB, darle el Wi-Fi y añadirla a Home Assistant; si se
  queda sin Wi-Fi, sigue funcionando **por el cable USB**.
- **Protocolos** a través de Home Assistant: ESPHome, MQTT, KNX, Zigbee, Matter, Z-Wave… y un puente para Alexa,
  Google y Apple (Matterbridge).
- **Conexiones externas**: comparte aparatos con otras plataformas mediante conectores instalables.
- **Módulos**: cada pestaña y bloque es un módulo que se activa, se apaga o se instala desde un archivo `.zip`
  (los submódulos cuelgan de su módulo, p. ej. cada conector de «Conexiones externas»).
- **Ayuda y presentaciones** guiadas dentro del propio programa.

## Instalar y abrir (con clics)
Necesitas **Docker Desktop** (Windows o macOS) o Docker (Linux).

1. Descarga o clona este repositorio.
2. Doble clic en **`iniciar_estudio.bat`** (Windows) o ejecuta **`./iniciar_estudio.sh`** (Linux, macOS).
   La primera vez prepara todo solo (Home Assistant, la voz, la IA y el Estudio); tarda unos minutos.
3. Abre **http://127.0.0.1:8765/studio/** y elige un proyecto.

Tus datos (proyectos, avance, módulos instalados, conexiones) se guardan en la carpeta **`project_studio_data`**, junto
a esta, y no en el repositorio. Las contraseñas y claves van aparte, en `~/.agents/secrets/project_studio/`.

Con una tarjeta gráfica NVIDIA, el lanzador usa la IA local con GPU; sin ella, con CPU o con el Ollama de tu equipo
(se elige en `stack/domotica-voz/.env`).

## Placa ESP32 (opcional)
Conecta la placa por USB y abre en el Estudio el proyecto «Domótica con voz» → pestaña **Aparatos** → bloque
**Placa**: instalar, conectar al Wi-Fi y añadir a Home Assistant, todo con botones. Para la línea de órdenes (sin
navegador) hay `uv run firmware/board.py` (ver `AGENTS.md`).

## Extender
- **Una pieza** nueva (sensor, placa, servicio) = un JSON en `catalog/components/`.
- **Un proyecto** nuevo = un JSON en `examples/projects/`.
- **Un módulo** (pestaña o bloque) = una carpeta con `module.json`; se instala desde **Módulos → Instalar (.zip)**.
- **Un conector** para otra plataforma = un submódulo de `conexiones` con `adds.connector` y un `translate.py`
  (tres funciones puras: `subscriptions`, `outgoing`, `incoming`).

La guía técnica (mapa del código, órdenes, códigos de error) está en **`AGENTS.md`**; los planes, en `docs/planes/`, y
lo pendiente, en `docs/backlog.md`.

## Pruebas
```
node --test tests/*/*.test.mjs
uv run --no-project --with pytest pytest tests/studio -q
uv run --no-project --with pytest --with httpx --with websockets pytest tests/server -q
```

## Arquitectura en una línea
Cebolla: reglas puras en `studio/domain/`, casos de uso en `studio/application/`, disco y red en
`studio/infrastructure/`, servidor y pantallas en `studio/presentation/`, `serve*.py` y `web/`. Una prueba revisa que
ninguna capa interior importe una exterior.

## Idioma
La interfaz está en español por defecto; los textos salen de `web/locales/<idioma>.json`. El código está en inglés.
