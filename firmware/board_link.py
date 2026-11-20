# Talks to the board over its «COM» port with the cable lines of cable.py: its state (Wi-Fi, IP) and its Wi-Fi.
# Used by board.py. Every function opens the port, does one exchange and closes it; failures raise BoardError.
import time

import serial

import cable

SAFE_BAUD = 115200  # flashing fallback (board.py)
LINK_BAUD = 921600  # the logger speed in packages/wifi.yaml (voice over the cable needs it)
STATUS_TIMEOUT_S, WIFI_TIMEOUT_S = 12, 60
NO_ANSWER = "La placa no responde. ¿Tiene el firmware del Estudio y el cable en «COM»?"


class BoardError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")


def open_port(port: str) -> serial.Serial:
    link = serial.Serial(baudrate=LINK_BAUD, timeout=0.2)
    link.port, link.dtr, link.rts = port, False, False  # low DTR/RTS would reset the board or hold it in boot mode
    try:
        link.open()
    except serial.SerialException as err:
        busy = "denied" in str(err).lower() or "permission" in str(err).lower()
        raise BoardError("E_PORT_BUSY" if busy else "E_PORT", f"No se pudo abrir {port}: "
                         + ("otro programa lo usa; ciérralo." if busy else "¿está conectada la placa?")) from err
    return link


def lines(link, timeout_s: float):
    """Yields the board's "@" lines (parsed) until timeout; log lines are skipped."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        found = cable.parse(link.readline())
        if found:
            yield found


def _wifi_state(link, timeout_s: float, want_online: bool = False) -> dict | None:
    for line in lines(link, timeout_s):
        if line["kind"] == "wifi" and (line["online"] or not want_online):
            return {"online": line["online"], "ip": line["ip"]}
    return None


def status(port: str) -> dict:
    """{"online": bool, "ip": str|None}: whether the board is on Wi-Fi (it answers over the cable either way)."""
    with open_port(port) as link:
        link.write(cable.GET_LINE)
        found = _wifi_state(link, STATUS_TIMEOUT_S)
    if found is None:
        raise BoardError("E_BOARD_SILENT", NO_ANSWER)
    return found


def wifi(port: str, ssid: str, password: str) -> str:
    with open_port(port) as link:
        link.write(cable.wifi_line(ssid, password))
        found = _wifi_state(link, WIFI_TIMEOUT_S, want_online=True)
    if not found or not found["ip"]:
        raise BoardError("E_WIFI_FAILED", "La placa no entró en la red en 60 s. Revisa el nombre y la clave, y que la "
                                          "red sea de 2,4 GHz (la placa no ve las de 5 GHz).")
    return f"OK: placa en {found['ip']}"
