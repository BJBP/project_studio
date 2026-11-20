# Cable mode on its own: while the Studio runs, a board plugged into its «COM» connector gets the cable bridge
# (which only takes over when Home Assistant cannot see the board). Unticking «🔌 Por cable» turns this off, ticking
# it turns it on again; the choice and the voice option are kept in the data folder (cable.json).
# start_watch(data_dir) starts the background check; remember(...) is called when the person ticks or unticks.
import json
import threading
import time
from pathlib import Path

import serve_board
import serve_jobs

PREFS_FILE = "cable.json"
DEFAULTS = {"auto": True, "project": "domotica-voz", "voice": "laptop"}
EVERY_S = 15


def load(data_dir: Path) -> dict:
    path = Path(data_dir) / PREFS_FILE
    saved = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return {**DEFAULTS, **saved}


def remember(data_dir: Path, on: bool, project: str, voice: str) -> None:
    path = Path(data_dir) / PREFS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"auto": bool(on), "project": project, "voice": voice}, indent=2), encoding="utf-8")


def port_to_start(prefs: dict, ports: list, states: dict) -> str | None:
    """The board's «COM» port when the bridge should start: auto on, nothing running, installing or using it."""
    if not prefs.get("auto"):
        return None
    for port in (p["port"] for p in ports if p.get("connector") == "com"):
        if "running" not in (states.get(f"cable:{port}"), states.get(f"flash:{port}"), states.get(f"busy:{port}")):
            return port
    return None


def tick(data_dir: Path) -> None:
    prefs = load(data_dir)
    if not prefs["auto"]:
        return
    code, found = serve_board.list_ports(Path(data_dir))  # its saved Wi-Fi name is not needed here
    ports = found.get("ports", []) if code == 200 else []
    states = {key: serve_jobs.status(key)["state"] for p in ports for key in (f"cable:{p['port']}", f"flash:{p['port']}")}
    states |= {f"busy:{p['port']}": "running" for p in ports if serve_board.port_busy(p["port"])}
    if port := port_to_start(prefs, ports, states):
        serve_board.start_cable(port, prefs["project"], prefs["voice"])


def start_watch(data_dir: Path) -> None:
    def loop():
        while True:
            try:
                tick(data_dir)
            except Exception as err:  # a failed check must not stop the Studio; the next one tries again
                print(f"AVISO E_CABLE_AUTO: {err}", flush=True)
            time.sleep(EVERY_S)
    threading.Thread(target=loop, daemon=True).start()
