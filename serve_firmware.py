# Compiles firmware from the Studio page without blocking it: start_build(name) runs firmware/build_firmware.py in
# the background; build_status(name) -> {"state": idle|running|ok|error, "message", "ready"}.
import re
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_SCRIPT = ROOT / "firmware" / "build_firmware.py"
NAME_RE = re.compile(r"^[a-z0-9_]+$")
_builds: dict = {}
_lock = threading.Lock()


def _ready(name: str) -> bool:
    return (ROOT / "web" / "firmware" / name / "manifest.json").exists()


def _run(name: str) -> None:
    done = subprocess.run([sys.executable, str(BUILD_SCRIPT), name], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    last = (done.stdout.strip().splitlines() or ["E_BUILD: sin salida"])[-1]
    with _lock:
        _builds[name] = {"state": "ok" if done.returncode == 0 else "error", "message": last}


def start_build(name: str) -> tuple[int, dict]:
    if not NAME_RE.match(str(name)) or not (ROOT / "firmware" / "esphome" / f"{name}.yaml").exists():
        return 400, {"code": "E_FIRMWARE_NAME", "message": f"No hay firmware «{name}»."}
    with _lock:
        if _builds.get(name, {}).get("state") == "running":
            return 200, build_status(name)[1]
        _builds[name] = {"state": "running", "message": "Compilando… (la primera vez tarda unos 10 minutos)"}
    threading.Thread(target=_run, args=(name,), daemon=True).start()
    return 202, build_status(name)[1]


def build_status(name: str) -> tuple[int, dict]:
    with _lock:
        status = dict(_builds.get(name, {"state": "idle", "message": ""}))
    return 200, {**status, "ready": _ready(name)}
