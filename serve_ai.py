# AI choices for the Studio page: lists the AIs of ai_providers.json and saves a cloud AI key, then runs the
# Home Assistant setup so its assistant appears. Keys stay in the secrets folder; the page never receives them.
# public_providers(secrets_dir) -> list;  save_key(secrets_dir, provider_id, key) -> {"ok": bool, "code", "message"}.
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROVIDERS_FILE = ROOT / "stack" / "domotica-voz" / "ai_providers.json"
SETUP_SCRIPT = ROOT / "stack" / "domotica-voz" / "setup" / "setup_ha.py"
SETUP_TIMEOUT_S = 180
MAX_KEY_LENGTH = 400


def _providers() -> list:
    return json.loads(PROVIDERS_FILE.read_text(encoding="utf-8"))["providers"]


def _keys(secrets_dir: Path) -> dict:
    path = secrets_dir / "ai_keys.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _write_keys(secrets_dir: Path, keys: dict) -> None:
    secrets_dir.mkdir(parents=True, exist_ok=True)
    (secrets_dir / "ai_keys.json").write_text(json.dumps(keys, indent=2), encoding="utf-8")


def public_providers(secrets_dir: Path) -> list:
    keys = _keys(secrets_dir)
    return [{"id": p["id"], "label": p["label"], "cloud": p["cloud"], "pipeline": p["pipeline"],
             "keyUrl": p.get("key_url"), "hasKey": p["id"] in keys} for p in _providers()]


def save_key(secrets_dir: Path, provider_id: str, key: str) -> dict:
    provider = next((p for p in _providers() if p["id"] == provider_id), None)
    key = str(key or "").strip()
    if not provider or not provider["cloud"]:
        return {"ok": False, "code": "E_PROVIDER", "message": "Esa IA no existe o no necesita clave."}
    if not key or len(key) > MAX_KEY_LENGTH or any(c.isspace() for c in key):
        return {"ok": False, "code": "E_KEY_FORMAT", "message": "La clave está vacía o tiene espacios. Cópiala otra vez."}
    keys = _keys(secrets_dir)
    previous = keys.get(provider_id)
    keys[provider_id] = key
    _write_keys(secrets_dir, keys)
    result = _run_setup(secrets_dir, provider_id)
    if not result["ok"]:  # a key HA rejected is not kept
        if previous:
            keys[provider_id] = previous
        else:
            keys.pop(provider_id)
        _write_keys(secrets_dir, keys)
    return result


def _run_setup(secrets_dir: Path, provider_id: str) -> dict:
    env = {**os.environ, "STUDIO_SECRETS": str(secrets_dir), "PYTHONIOENCODING": "utf-8"}
    try:
        done = subprocess.run(["uv", "run", str(SETUP_SCRIPT)], env=env, capture_output=True, text=True,
                              encoding="utf-8", timeout=SETUP_TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as err:
        return {"ok": False, "code": "E_SETUP", "message": f"No terminó la configuración de Home Assistant ({err})."}
    lines = done.stdout.strip().splitlines()
    warning = next((ln for ln in lines if ln.startswith(f"AVISO {provider_id} ")), None)
    if warning:
        code, _, message = warning.split(" ", 2)[2].partition(": ")
        return {"ok": False, "code": code, "message": message}
    if done.returncode != 0:
        print(done.stdout, done.stderr, file=sys.stderr)
        return {"ok": False, "code": "E_SETUP", "message": (lines or ["Falló la configuración."])[-1]}
    return {"ok": True, "code": None, "message": "Listo."}
