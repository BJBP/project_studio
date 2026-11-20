#!/usr/bin/env bash
# Starts the Studio, all in Docker (Linux/macOS): voice stack, local AI, Home Assistant setup and the Studio.
# Needs only Docker. The first time it downloads several GB and takes a while.
set -euo pipefail
cd "$(dirname "$0")"
STACK=stack/domotica-voz
[ -f "$STACK/.env" ] || cp "$STACK/.env.example" "$STACK/.env"
[ -f .env ] || cp .env.example .env
set -a; . "$STACK/.env"; . ./.env; set +a
STUDIO_PORT="${STUDIO_PORT:-8765}"
echo "Project Studio"
docker info >/dev/null 2>&1 || { echo "[E_DOCKER_DOWN] Arranca Docker y repite."; exit 1; }
echo "Docker listo."
# The two folders Docker mounts, as your user; everything inside them is made by the init service.
mkdir -p ../project_studio_data "$HOME/.agents/secrets/project_studio"
export STUDIO_UID="${STUDIO_UID:-$(id -u)}" STUDIO_GID="${STUDIO_GID:-$(id -g)}"
# An NVIDIA card runs the local AI much faster: switch the default "cpu" to "gpu".
if [ "${COMPOSE_PROFILES:-}" = cpu ] && command -v nvidia-smi >/dev/null; then export COMPOSE_PROFILES=gpu; fi
COMPOSE=(docker compose --env-file "$STACK/.env" --env-file .env)
"${COMPOSE[@]}" run --rm --build init || { echo "[E_INIT] No se crearon las carpetas y claves."; exit 1; }
echo "Arrancando (la primera vez descarga varios GB y tarda)..."
"${COMPOSE[@]}" up -d --build || { echo "[E_SETUP] No arrancó. Mira: docker compose logs setup"; exit 1; }
URL="http://127.0.0.1:${STUDIO_PORT}/studio/"
echo "Abriendo el Estudio en $URL"
(command -v xdg-open >/dev/null && xdg-open "$URL" || open "$URL") >/dev/null 2>&1 &
