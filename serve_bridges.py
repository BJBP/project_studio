# Bridges the Studio runs next to Home Assistant, as background jobs: today Matterbridge (Alexa, Google and Apple
# through Matter). bridge(name, on) starts or stops one; bridge_status(name) -> serve_jobs.status (its last line).
import shutil
from pathlib import Path

import serve_jobs

SETUP = Path(__file__).resolve().parent / "stack" / "domotica-voz" / "setup"
BRIDGES = {"matterbridge": [SETUP / "matterbridge.py", "start"]}


def bridge_status(name: str) -> tuple[int, dict]:
    if name not in BRIDGES:
        return 404, {"code": "E_UNKNOWN_BRIDGE", "message": f"No hay puente «{name}»."}
    return 200, serve_jobs.status(f"bridge:{name}")


def bridge(name: str, on: bool) -> tuple[int, dict]:
    if name not in BRIDGES:
        return 404, {"code": "E_UNKNOWN_BRIDGE", "message": f"No hay puente «{name}»."}
    if on:
        script, *args = BRIDGES[name]
        serve_jobs.start(f"bridge:{name}", [shutil.which("uv") or "uv", "run", "--quiet", str(script), *args],
                         "Arrancando…", live=True)
    else:
        serve_jobs.stop(f"bridge:{name}")
    return bridge_status(name)
