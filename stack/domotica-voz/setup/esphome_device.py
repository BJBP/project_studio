# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27", "websockets>=12"]
# ///
# Adds an ESPHome device (real or simulated) to Home Assistant with the API encryption key from the secrets folder.
# Usage: uv run stack/domotica-voz/setup/esphome_device.py [host] [port]   (default esp32-sim 6053)
# Exit 0 = added or already there; otherwise "<CODE>: <what to do>". The key is never printed.
import json
import os
import sys
from pathlib import Path

from flows import run_flow
from ha_client import HaClient, HaError

SECRETS_DIR = Path(os.environ.get("STUDIO_SECRETS", Path.home() / ".agents" / "secrets" / "project_studio"))
BASE_URL = os.environ.get("HA_URL", "http://127.0.0.1:8123")


def api_key() -> str:
    """api_encryption_key from esphome_secrets.yaml (one "name: value" per line)."""
    for line in (SECRETS_DIR / "esphome_secrets.yaml").read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition(":")
        if key.strip() == "api_encryption_key":
            return value.strip().strip('"').strip("'")
    raise HaError("E_NO_SECRETS", "Falta api_encryption_key en esphome_secrets.yaml.")


def main(argv: list) -> int:
    host = argv[0] if argv else "esp32-sim"
    port = int(argv[1]) if len(argv) > 1 else 6053
    try:
        token = json.loads((SECRETS_DIR / "ha.json").read_text(encoding="utf-8"))["token"]
        client = HaClient(BASE_URL, token)
        result = run_flow(client, "esphome", {"user": {"host": host, "port": port},
                                              "encryption_key": {"noise_psk": api_key()}})
    except (HaError, OSError) as err:
        print(err)
        return 1
    print(f"OK: {host}:{port} en Home Assistant ({result.get('title') or result.get('reason')})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
