# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27", "websockets>=12"]
# ///
# Alexa, Google Home and Apple Home reach the house through Matter: Matterbridge (Apache 2.0, Node) shows them the
# Home Assistant entities the voice assistant sees. Usage:
#   uv run matterbridge.py install   npm installs the pinned versions in <data>/apps/matterbridge
#   uv run matterbridge.py start     writes the plugin config (HA token, entity list) and runs Matterbridge
# Its page (QR code to pair from the Alexa or Google app): http://127.0.0.1:8283. Prints "OK: ..." or "<CODE>: ...".
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from ha_client import HaClient, HaError

VERSIONS = {"matterbridge": "3.11.4", "matterbridge-hass": "1.7.0"}
REPO = Path(__file__).resolve().parents[3]
APP_DIR = Path(os.environ.get("STUDIO_DATA", REPO.parent / "project_studio_data")) / "apps" / "matterbridge"
SECRETS = Path(os.environ.get("STUDIO_SECRETS", Path.home() / ".agents" / "secrets" / "project_studio"))
HOME_DIR = SECRETS / "matterbridge"  # its config holds the Home Assistant token, and the Matter pairing
HA_URL = os.environ.get("HA_URL", "http://127.0.0.1:8124")
FRONTEND_PORT = os.environ.get("MATTERBRIDGE_PORT", "8283")


def bridge_config(ha_url: str, token: str, exposed: dict) -> dict:
    """matterbridge-hass settings: only the entities exposed to the voice assistant reach Alexa and Google."""
    entities = sorted(e for e, assistants in exposed.items() if assistants.get("conversation"))
    return {"name": "matterbridge-hass", "type": "DynamicPlatform", "host": ha_url.replace("http", "ws", 1),
            "token": token, "rejectUnauthorized": True, "entityWhiteList": entities, "whiteList": [],
            "blackList": [], "entityBlackList": [], "discardHiddenEntities": True, "debug": False,
            "unregisterOnShutdown": False}


def npm() -> str:
    found = shutil.which("npm")
    if not found:
        raise HaError("E_NO_NODE", "Falta Node.js (npm). Instálalo desde nodejs.org y repite.")
    return found


def install() -> str:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if not (APP_DIR / "package.json").exists():
        (APP_DIR / "package.json").write_text('{"private": true}\n', encoding="utf-8")
    packages = [f"{name}@{version}" for name, version in VERSIONS.items()]
    done = subprocess.run([npm(), "install", "--no-fund", "--no-audit", *packages], cwd=APP_DIR)
    if done.returncode:
        raise HaError("E_NPM", "npm no pudo instalar Matterbridge; revisa la conexión y repite.")
    return f"OK: Matterbridge {VERSIONS['matterbridge']} en {APP_DIR}"


def start() -> int:
    plugin = APP_DIR / "node_modules" / "matterbridge-hass"
    if not plugin.exists():
        raise HaError("E_NOT_INSTALLED", "Matterbridge no está instalado: uv run matterbridge.py install")
    token = json.loads((SECRETS / "ha.json").read_text(encoding="utf-8"))["token"]
    exposed = HaClient(HA_URL, token).ws({"type": "homeassistant/expose_entity/list"})[0]["exposed_entities"]
    config_dir = HOME_DIR / ".matterbridge"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "matterbridge-hass.config.json").write_text(
        json.dumps(bridge_config(HA_URL, token, exposed), indent=2), encoding="utf-8")
    run = [shutil.which("node") or "node", str(APP_DIR / "node_modules" / "matterbridge" / "bin" / "matterbridge.js"),
           "--homedir", str(HOME_DIR), "--frontend", FRONTEND_PORT, "--bind", "127.0.0.1"]
    # The plugin finds matterbridge in the same node_modules; its "npm link" hangs on Windows and is not needed.
    env = {**os.environ, "MATTERBRIDGE_LINK_LOCAL_PLUGINS": "false"}
    subprocess.run([*run, "--add", str(plugin)], cwd=APP_DIR, env=env, capture_output=True)  # repeats are harmless
    print(f"OK: Matterbridge en http://127.0.0.1:{FRONTEND_PORT} (escanea su QR desde la app de Alexa o Google)",
          flush=True)
    with open(HOME_DIR / "matterbridge.log", "w", encoding="utf-8") as log:  # the Studio shows only our own lines
        return subprocess.run(run, cwd=APP_DIR, env=env, stdout=log, stderr=subprocess.STDOUT).returncode


def main(argv: list) -> int:
    try:
        if argv == ["install"]:
            print(install())
            return 0
        if argv == ["start"]:
            return start()
        print("E_ARGS: uso: matterbridge.py install | start")
    except (HaError, OSError, KeyError) as err:
        print(err)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
