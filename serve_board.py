# Real board from the Studio page: ports, install in the background, the board's state, Wi-Fi + Home Assistant in one
# step (add_to_ha alone for a board that already has Wi-Fi), and cable mode (firmware/cable_bridge.py, which holds
# the port: the other actions pause it and resume it). Runs firmware/board.py (needs uv);
# the Wi-Fi password goes by stdin and is never logged. Each function returns (http_status, json).
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import serve_jobs

ROOT = Path(__file__).resolve().parent
BOARD = ROOT / "firmware" / "board.py"
CABLE_BRIDGE = ROOT / "firmware" / "cable_bridge.py"
ADD_TO_HA = ROOT / "stack" / "domotica-voz" / "setup" / "esphome_device.py"
NAME_DEVICES = ROOT / "stack" / "domotica-voz" / "setup" / "device_names.py"
PROJECT_RE = re.compile(r"^[a-z0-9-]+$")
PORT_RE = re.compile(r"^(COM\d{1,3}|/dev/tty[\w.-]+|/dev/cu\.[\w.-]+)$")
NAME_RE = re.compile(r"^[a-z0-9_]+$")
IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
OK_IP = re.compile(r"^OK: placa en (\d+\.\d+\.\d+\.\d+)$")
WIFI_FILE = "wifi.json"
_cable_projects: dict = {}  # port -> project, while cable mode is on


def _board(args: list, stdin: str | None = None, timeout_s: int = 120) -> tuple[int, str]:
    uv = shutil.which("uv")
    if not uv:
        return 1, "E_NO_UV: falta uv en este equipo (el Estudio en Docker no ve el USB: usa «⚡ Instalar por USB»)."
    try:
        done = subprocess.run([uv, "run", "--quiet", str(BOARD), *args], input=stdin, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return 1, "E_BOARD_TIMEOUT: la placa tardó demasiado en responder."
    return done.returncode, (done.stdout.strip().splitlines() or ["E_BOARD: sin salida"])[-1]


def _error(line: str) -> tuple[int, dict]:
    code, _, message = line.partition(": ")
    return 400, {"code": code, "message": message or line}


def list_ports(secrets_dir: Path) -> tuple[int, dict]:
    code, line = _board(["ports"], timeout_s=60)
    if code:
        return _error(line)
    saved = secrets_dir / WIFI_FILE
    ssid = json.loads(saved.read_text(encoding="utf-8")).get("ssid") if saved.exists() else None
    return 200, {"ports": json.loads(line), "savedSsid": ssid}


def _cable_key(port: str) -> str:
    return f"cable:{port}"


def start_cable(port: str, project: str) -> tuple[int, dict]:
    if not PORT_RE.match(str(port)) or not PROJECT_RE.match(str(project)):
        return 400, {"code": "E_BOARD_ARGS", "message": "Puerto o proyecto no válidos."}
    _cable_projects[port] = project
    serve_jobs.start(_cable_key(port), [shutil.which("uv") or "uv", "run", "--quiet", str(CABLE_BRIDGE), "--port", port,
                                        "--project", project], "Conectando por cable…", live=True)
    return cable_status(port)


def stop_cable(port: str) -> tuple[int, dict]:
    project = _cable_projects.pop(port, None)
    if serve_jobs.stop(_cable_key(port)) and project:
        # The bridge is killed without cleaning up: take its stand-in out and show the Wi-Fi entities to the voice.
        subprocess.run([shutil.which("uv") or "uv", "run", "--quiet", str(CABLE_BRIDGE), "--restore", "--project", project],
                       capture_output=True, timeout=120)
    return cable_status(port)


def cable_status(port: str) -> tuple[int, dict]:
    return 200, serve_jobs.status(_cable_key(port))


def _port_free(port: str, action):
    """Runs action() with the cable bridge paused (it holds the port), then resumes it."""
    project = _cable_projects.get(port)
    paused = serve_jobs.stop(_cable_key(port))
    try:
        return action()
    finally:
        if paused and project:
            start_cable(port, project)


def start_flash(name: str, port: str) -> tuple[int, dict]:
    if not NAME_RE.match(str(name)) or not PORT_RE.match(str(port)):
        return 400, {"code": "E_BOARD_ARGS", "message": "Firmware o puerto no válidos."}
    stop_cable(port)  # installing resets the board; cable mode is turned on again from the page
    uv = shutil.which("uv") or "uv"
    serve_jobs.start(f"flash:{port}", [uv, "run", "--quiet", str(BOARD), "flash", name, "--port", port],
                     "Instalando… (unos 2 minutos; no desconectes el cable)")
    return flash_status(port)


def flash_status(port: str) -> tuple[int, dict]:
    return 200, serve_jobs.status(f"flash:{port}")


def board_status(port: str) -> tuple[int, dict]:
    if not PORT_RE.match(str(port)):
        return 400, {"code": "E_BOARD_ARGS", "message": "Puerto no válido."}
    code, line = _port_free(port, lambda: _board(["status", "--port", port], timeout_s=60))
    return _error(line) if code else (200, json.loads(line))  # {"online", "ip"}


def connect(secrets_dir: Path, port: str, ssid: str, password: str, remember: bool, project: str) -> tuple[int, dict]:
    """Gives the board the Wi-Fi and adds it to Home Assistant. With no password, uses the remembered one."""
    if not PORT_RE.match(str(port)):
        return 400, {"code": "E_BOARD_ARGS", "message": "Puerto no válido."}
    saved = secrets_dir / WIFI_FILE
    if not password and saved.exists():
        credentials = json.loads(saved.read_text(encoding="utf-8"))
    else:
        credentials = {"ssid": ssid, "password": password}
    code, line = _port_free(port, lambda: _board(["wifi", "--port", port, "--stdin"], stdin=json.dumps(credentials),
                                                 timeout_s=120))
    match = OK_IP.match(line)
    if code or not match:
        return _error(line)
    if remember:
        secrets_dir.mkdir(parents=True, exist_ok=True)
        saved.write_text(json.dumps(credentials), encoding="utf-8")
    return add_to_ha(match.group(1), project)


def add_to_ha(ip: str, project: str) -> tuple[int, dict]:
    if not IP_RE.match(str(ip)):
        return 400, {"code": "E_BOARD_ARGS", "message": "Dirección no válida."}
    ha = subprocess.run([shutil.which("uv") or "uv", "run", "--quiet", str(ADD_TO_HA), ip], capture_output=True,
                        text=True, encoding="utf-8", errors="replace", env=os.environ.copy(), timeout=120)
    ha_line = (ha.stdout.strip().splitlines() or ["E_HA: sin salida"])[-1]
    if ha.returncode == 0:
        sync_names(project)  # the board takes the plain names; its virtual twin becomes "… virtual"
    return 200, {"ip": ip, "inHomeAssistant": ha.returncode == 0, "message": ha_line}


def sync_names(project: str) -> tuple[int, dict]:
    """Names in Home Assistant: real board vs virtual twin, and the names chosen for each output."""
    if not PROJECT_RE.match(str(project)):
        return 400, {"code": "E_BOARD_ARGS", "message": "Proyecto no válido."}
    done = subprocess.run([shutil.which("uv") or "uv", "run", "--quiet", str(NAME_DEVICES), project], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=os.environ.copy(), timeout=120)
    line = (done.stdout.strip().splitlines() or ["E_NAMES: sin salida"])[-1]
    return (200, {"message": line}) if done.returncode == 0 else _error(line)
