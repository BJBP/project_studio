# Compiles firmware from the Studio page without blocking it: start_build(name) runs firmware/build_firmware.py in
# the background; build_status(name) -> {"state": idle|running|ok|error, "message", "ready"}.
import re
import sys
from pathlib import Path

import serve_jobs

ROOT = Path(__file__).resolve().parent
BUILD_SCRIPT = ROOT / "firmware" / "build_firmware.py"
NAME_RE = re.compile(r"^[a-z0-9_]+$")


def _ready(name: str) -> bool:
    return (ROOT / "web" / "firmware" / name / "manifest.json").exists()


def start_build(name: str) -> tuple[int, dict]:
    if not NAME_RE.match(str(name)) or not (ROOT / "firmware" / "esphome" / f"{name}.yaml").exists():
        return 400, {"code": "E_FIRMWARE_NAME", "message": f"No hay firmware «{name}»."}
    started = serve_jobs.start(f"build:{name}", [sys.executable, str(BUILD_SCRIPT), name],
                               "Compilando… (la primera vez tarda unos 10 minutos)")
    return (202 if started else 200), build_status(name)[1]


def build_status(name: str) -> tuple[int, dict]:
    return 200, {**serve_jobs.status(f"build:{name}"), "ready": _ready(name)}
