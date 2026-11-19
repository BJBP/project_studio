# /// script
# requires-python = ">=3.11"
# dependencies = ["pyserial>=3.5", "esptool>=5"]
# ///
# Real board over the USB cable, without a browser: list ports, install the firmware, give it the Wi-Fi (cable lines,
# cable.py), and keep it in Home Assistant over the cable while it has no Wi-Fi (cable_bridge.py).
# Usage: uv run firmware/board.py ports | flash <name> --port COM4 | status|wifi --port COM4 [--stdin]
# wifi reads {"ssid","password"} from stdin (--stdin) or from <secrets>/wifi.json; the password is never printed.
# Exit 0 = "OK: ..." (ports/status print JSON); otherwise "<CODE>: <what to do>".
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from serial.tools import list_ports

from board_link import SAFE_BAUD, BoardError, status, wifi

ROOT = Path(__file__).resolve().parents[1]
SECRETS_DIR = Path(os.environ.get("STUDIO_SECRETS", Path.home() / ".agents" / "secrets" / "project_studio"))
USB_SERIAL_CHIPS = {0x1A86: "CH34x", 0x10C4: "CP210x", 0x0403: "FTDI"}  # «COM» connector: separate USB-serial chip
ESPRESSIF_VID = 0x303A  # chip's own USB
FAST_BAUD = 921600


def ports() -> list:
    found = []
    for port in list_ports.comports():
        connector = "com" if port.vid in USB_SERIAL_CHIPS else "usb" if port.vid == ESPRESSIF_VID else None
        if connector:
            found.append({"port": port.device, "connector": connector, "chip": USB_SERIAL_CHIPS.get(port.vid, "ESP32")})
    return found


def flash(name: str, port: str) -> str:
    image = ROOT / "web" / "firmware" / name / "firmware.factory.bin"
    if not image.exists():
        raise BoardError("E_NO_FIRMWARE", f"No hay firmware «{name}» compilado. Pulsa «Compilar» primero.")
    for baud in (FAST_BAUD, SAFE_BAUD):
        # --no-stub: the esptool helper program fails on some USB-serial chips (CH343) at these speeds.
        done = subprocess.run([sys.executable, "-m", "esptool", "--port", port, "--baud", str(baud), "--no-stub",
                               "write-flash", "0x0", str(image)], text=True, encoding="utf-8", errors="replace")
        if done.returncode == 0:
            return f"OK: firmware {name} instalado en {port}"
    raise BoardError("E_FLASH", f"No se pudo instalar en {port}. Revisa el cable en el conector «COM» y que ningún "
                                "otro programa use el puerto; si sigue, mantén BOOT, pulsa RESET y suelta BOOT.")


def credentials(from_stdin: bool) -> tuple[str, str]:
    try:
        data = json.loads(sys.stdin.read() if from_stdin else (SECRETS_DIR / "wifi.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise BoardError("E_NO_WIFI_SECRETS", "Falta el Wi-Fi: escríbelo en Aparatos → Wi-Fi de la placa.") from err
    ssid, password = str(data.get("ssid", "")), str(data.get("password", ""))
    if not 0 < len(ssid.encode()) <= 32 or len(password.encode()) > 64:
        raise BoardError("E_WIFI_FORMAT", "El nombre de la red va de 1 a 32 letras y la clave hasta 64.")
    return ssid, password


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(prog="board.py")
    parser.add_argument("action", choices=["ports", "flash", "status", "wifi"])
    parser.add_argument("name", nargs="?", default="circuito_maestro")
    parser.add_argument("--port")
    parser.add_argument("--stdin", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.action == "ports":
            print(json.dumps(ports()))
            return 0
        if not args.port:
            raise BoardError("E_NO_PORT", "Falta --port (mira los puertos con: board.py ports).")
        if args.action == "flash":
            print(flash(args.name, args.port))
        elif args.action == "status":
            print(json.dumps(status(args.port)))
        else:
            print(wifi(args.port, *credentials(args.stdin)))
    except BoardError as err:
        print(err)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
