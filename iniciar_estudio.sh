#!/usr/bin/env bash
# Starts the Studio: Docker stack, local AI model, Home Assistant setup, web server and browser (Linux/macOS).
set -euo pipefail
cd "$(dirname "$0")"
STACK=stack/domotica-voz
[ -f "$STACK/.env" ] || cp "$STACK/.env.example" "$STACK/.env"
set -a; . "$STACK/.env"; set +a
export HA_URL="http://127.0.0.1:${HA_PORT}" MQTT_WS_URL="ws://127.0.0.1:${MQTT_WS_PORT}"
STUDIO_PORT="${STUDIO_PORT:-8765}"
command -v uv >/dev/null || { echo "[E_NO_UV] Falta uv: https://docs.astral.sh/uv/"; exit 1; }
command -v ollama >/dev/null || { echo "[E_NO_OLLAMA] Falta Ollama: https://ollama.com"; exit 1; }
docker info >/dev/null 2>&1 || { echo "[E_DOCKER_DOWN] Arranca Docker y repite."; exit 1; }
uv run "$STACK/setup/ensure_secrets.py"
docker compose -f "$STACK/docker-compose.yml" --env-file "$STACK/.env" up -d
ollama list | grep -q "^${OLLAMA_MODEL}" || ollama pull "$OLLAMA_MODEL"
uv run "$STACK/setup/setup_ha.py"
URL="http://127.0.0.1:${STUDIO_PORT}/studio/"
(command -v xdg-open >/dev/null && xdg-open "$URL" || open "$URL") >/dev/null 2>&1 &
uv run --no-project python serve.py --port "$STUDIO_PORT"
