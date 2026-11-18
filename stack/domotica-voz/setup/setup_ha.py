# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27", "websockets>=12"]
# ///
# Configures a fresh Home Assistant for the voice demo: test user, MQTT, Whisper, Piper, Ollama, voice pipeline.
# Receives settings from environment variables; writes the access token to the secrets folder (outside the repo).
# Exit code 0 = ready; otherwise prints "<CODE>: <what to do>".
import json
import os
import secrets
import sys
import time
from pathlib import Path

import httpx

from flows import ensure_integrations, ensure_pipeline
from ha_client import HaClient, HaError

BASE_URL = os.environ.get("HA_URL", "http://127.0.0.1:8123")
SECRETS_FILE = Path(os.environ.get("STUDIO_SECRETS", Path.home() / ".agents" / "secrets" / "project_studio")) / "ha.json"
CLIENT_ID = BASE_URL + "/"


def wait_for_ha(timeout_s: int = 300) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            if httpx.get(f"{BASE_URL}/api/onboarding", timeout=5).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(3)
    raise HaError("E_HA_DOWN", f"Home Assistant no arrancó en {timeout_s} s. Revisa: docker compose logs homeassistant")


def onboard() -> dict:
    steps = {s["step"]: s["done"] for s in httpx.get(f"{BASE_URL}/api/onboarding", timeout=10).json()}
    if steps.get("user"):
        raise HaError("E_HA_ONBOARDED", f"Home Assistant ya tiene usuario pero falta {SECRETS_FILE}. "
                      "Borra el volumen ha_config (docker compose down -v) y repite.")
    creds = {"username": "demo", "password": secrets.token_urlsafe(18)}
    anon = HaClient(BASE_URL)
    code = anon.post("/api/onboarding/users", {"client_id": CLIENT_ID, "name": "Demo", "language": "es", **creds})["auth_code"]
    tokens = anon.post("/auth/token", {"grant_type": "authorization_code", "code": code, "client_id": CLIENT_ID}, form=True)
    user = HaClient(BASE_URL, tokens["access_token"])
    user.post("/api/onboarding/core_config")
    user.post("/api/onboarding/analytics")
    user.post("/api/onboarding/integration", {"client_id": CLIENT_ID, "redirect_uri": CLIENT_ID})
    long_lived = user.ws({"type": "auth/long_lived_access_token", "client_name": "project-studio", "lifespan": 3650})[0]
    return {**creds, "token": long_lived, "url": BASE_URL}


def load_or_create_secrets() -> dict:
    if SECRETS_FILE.exists():
        return json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
    data = onboard()
    SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SECRETS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def main() -> int:
    try:
        wait_for_ha()
        data = load_or_create_secrets()
        client = HaClient(BASE_URL, data["token"])
        ensure_integrations(client)
        ensure_pipeline(client)
    except HaError as err:
        print(err)
        return 1
    print(f"OK: Home Assistant listo en {BASE_URL}. Token en {SECRETS_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
