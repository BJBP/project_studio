# Todo en Docker: el Estudio funciona igual en Windows, Linux y macOS

Estado: **pendiente** (2026-11-20): la persona usuaria lo dejó en espera; faltan las 4 decisiones pendientes.

## Objetivo
Un solo `docker compose up -d` en la raíz del repositorio arranca todo: el stack de voz, Ollama, la configuración de
Home Assistant y el Estudio. El equipo solo necesita Docker (Docker Desktop en Windows y macOS). Lo que corre dentro de
los contenedores es Linux en los tres sistemas, así que basta con probarlo en Linux (GitHub Actions) para que valga
para todos. Hoy, en cambio, hacen falta `uv` y Ollama instalados aparte, y cada lanzador hace 6 pasos a su manera.

## Decisiones aprobadas
- Meter en Docker todo lo que se pueda; lo que dependa del equipo queda como opción documentada.
- Ollama pasa a ser un contenedor del stack (`ollama/ollama`). Desaparecen el puente `ollama-bridge` (Linux) y el
  ajuste de Ollama en `0.0.0.0` (Windows).
- El Estudio pasa a ser un contenedor por defecto; el compose de la raíz incluye el del stack (`include:`).
- La configuración de Home Assistant (`setup_ha.py`) corre en un contenedor de un solo uso del compose.
- Los lanzadores `.bat` y `.sh` quedan en lo mínimo: comprobar Docker, `docker compose up -d` y abrir el navegador.

## Decisiones pendientes
1. **Modelos de Ollama: volumen propio o los del equipo.** Recomendado: volumen propio (`ollama_data`). Es igual en
   todos los sistemas; coste: el modelo (~3,3 GB) se descarga una vez más si ya estaba en el Ollama del equipo.
2. **Mac sin GPU en Docker.** Recomendado: Ollama en contenedor por defecto (va lento en Mac, pero funciona) y una
   variable `OLLAMA_URL` en `.env` para usar el Ollama instalado en el Mac, con su GPU. En Windows (NVIDIA) y Linux,
   el contenedor usa la GPU con el profile `gpu`.
3. **Lo que el Estudio hace con Docker desde dentro** (reiniciar el detector de palabra para despertar y compilar el
   firmware). Opciones:
   - a) Montar el socket de Docker en el contenedor del Estudio. Simple, pero el Estudio queda con control total del
     Docker del equipo (equivale a root).
   - b) **Recomendado:** un `docker-socket-proxy` que solo deja reiniciar contenedores y lanzar el de compilación.
     Coste: un servicio más (~10 MB).
   - c) Quitar esas dos funciones del Estudio en Docker y dejarlas para el lanzador con `uv`.
4. **Placa por USB.** Docker en Windows y Mac no ve bien el USB. Recomendado: instalar el firmware desde el navegador
   (ESP Web Tools, ya existe: «⚡ Instalar por USB») y dejar el modo cable (`cable_bridge.py`) y `board.py` como
   herramientas opcionales del equipo, que siguen necesitando `uv`. El Estudio ya avisa (`E_NO_UV`).

## Mockup

Lanzador (`iniciar_estudio.bat` / `.sh`), consola:
```
Project Studio
✓ Docker listo
⟳ Arrancando (la primera vez descarga ~9 GB y tarda)…
  homeassistant ✓  mqtt ✓  whisper ✓  piper ✓  ollama ✓  estudio ✓
⟳ Configurando Home Assistant… ✓
→ Abriendo http://127.0.0.1:8765/studio/

Estados de error:
✗ [E_DOCKER_DOWN] Docker no está arrancado. Abre Docker Desktop y repite.
✗ [E_SETUP] Home Assistant no se configuró: <línea del contenedor setup>. Ver: docker compose logs setup
✗ [E_PORT_BUSY] El puerto 8765 está ocupado. Cambia STUDIO_PORT en .env.
```

Estudio, bloque «Placa» (sin cambios de diseño; texto cuando el Estudio corre en Docker):
```
┌ Placa ───────────────────────────────────────────┐
│ [⚡ Instalar por USB]  ← desde el navegador        │
│ ℹ Modo cable y estado por USB: necesitan el        │
│   Estudio fuera de Docker (ver Ayuda → Placa)      │
└──────────────────────────────────────────────────┘
```

## Ejemplos de uso
- Con clics: doble clic en `iniciar_estudio.bat` (Windows) o `iniciar_estudio.sh` (Linux/macOS).
- Línea de comandos, en la raíz: `docker compose up -d` y abrir http://127.0.0.1:8765/studio/.
- Con GPU NVIDIA: `COMPOSE_PROFILES=gpu docker compose up -d` (o `COMPOSE_PROFILES=gpu` en `.env`).
- Mac con el Ollama del equipo: `OLLAMA_URL=http://host.docker.internal:11434` en `.env`.
- Ver qué pasó al configurar: `docker compose logs setup`.
- Parar: `docker compose down` (los datos quedan en volúmenes y en `../project_studio_data`).

## Fases
1. **Ollama en el stack.** Servicio `ollama` (volumen `ollama_data`, sin puerto publicado salvo opción), servicio de un
   solo uso `ollama-pull` que descarga `OLLAMA_MODEL`, profile `gpu` con la GPU NVIDIA. `flows.py`, `agents.py` y
   `serve_models.py` usan `http://ollama:11434` por defecto. Se quita `ollama-bridge`.
2. **Configuración de Home Assistant en un contenedor.** Servicio `setup` (imagen `uv`, ejecuta `setup_ha.py` con
   reintentos hasta que HA responda) que depende de `homeassistant` y `ollama-pull`. Escribe `ha.json` en la carpeta de
   secretos con el usuario del equipo (`STUDIO_UID`).
3. **Un solo compose.** `docker-compose.yml` de la raíz incluye `stack/domotica-voz/docker-compose.yml`; el Estudio
   arranca después de `setup`. Se mantiene `docker compose -f stack/...` para quien solo quiera el stack.
4. **Carpetas del equipo sin `uv`.** Servicio de un solo uso `init` (como `STUDIO_UID`) que crea `esphome_secrets.yaml`
   y las carpetas dentro de las que monta. Los lanzadores solo hacen `mkdir` de las dos carpetas raíz (datos y
   secretos), que en `.bat` y `.sh` es una línea. Comprobar que Compose crea `esphome` después de `init`; si no,
   ESPHome monta la carpeta de secretos y no el archivo.
5. **Docker desde el Estudio** según la decisión 3.
6. **Lanzadores mínimos** (mockup) y Ayuda → Placa con el texto del modo cable.
7. **GitHub Actions.** Linux: `docker compose up -d` completo (sin GPU, con un modelo pequeño), espera a `setup`,
   pruebas de Python y Node, y una orden escrita de extremo a extremo (`tests/e2e/`). Windows y macOS: pruebas de
   Python y Node, `docker compose config` y que el `.bat`/`.sh` no tengan errores de sintaxis. Comprobar saltos de línea.

## Archivos
- `docker-compose.yml` (raíz): `include`, servicios `init`, `setup`, `studio`; red y dependencias.
- `stack/domotica-voz/docker-compose.yml`: `ollama`, `ollama-pull`, profile `gpu`; fuera `ollama-bridge`.
- `stack/domotica-voz/setup/{flows,agents,setup_ha,ensure_host_paths}.py`, `serve_models.py`, `serve_wake.py`,
  `serve_firmware.py`, `firmware/build_firmware.py`.
- `iniciar_estudio.bat`, `iniciar_estudio.sh`, `.env.example` (raíz y stack), `Dockerfile`.
- `.github/workflows/pruebas.yml` (nuevo), `AGENTS.md` (flujo y mapa), `docs/backlog.md`.

## Verificación
- Linux (este equipo): borrar volúmenes de prueba, doble clic en el lanzador y llegar al Estudio con la Demo conectada;
  orden escrita «enciende el foco» → cambia el estado en Home Assistant; voz con micrófono.
- Con `COMPOSE_PROFILES=gpu`: Ollama usa la GPU (`docker compose exec ollama nvidia-smi` o `ollama ps`).
- Los archivos de `../project_studio_data` y de la carpeta de secretos quedan a nombre del usuario.
- GitHub Actions en verde en los tres sistemas.
- Windows y macOS reales: una sola vez al terminar, doble clic en el lanzador (lo único que no cubre la CI).

## Estimación
Medio día a un día. Las fases 1–4 son lo principal; la 5 depende de la decisión 3; la 7, unas 2 horas.
