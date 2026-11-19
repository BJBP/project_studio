# Talks Improv Serial with a board over its «COM» port: its state (online, IP), the networks it sees, and the Wi-Fi.
# Used by board.py. Every function opens the port, does one exchange and closes it; failures raise BoardError.
import time

import serial

import improv

SAFE_BAUD = 115200
SCAN_TIMEOUT_S, WIFI_TIMEOUT_S, STATE_TIMEOUT_S, STATE_RETRY_S = 15, 60, 30, 3


class BoardError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")


def open_port(port: str) -> serial.Serial:
    link = serial.Serial(baudrate=SAFE_BAUD, timeout=0.2)
    link.port, link.dtr, link.rts = port, False, False  # low DTR/RTS would reset the board or hold it in boot mode
    try:
        link.open()
    except serial.SerialException as err:
        busy = "denied" in str(err).lower() or "permission" in str(err).lower()
        raise BoardError("E_PORT_BUSY" if busy else "E_PORT", f"No se pudo abrir {port}: "
                         + ("otro programa lo usa; ciérralo." if busy else "¿está conectada la placa?")) from err
    return link


def _packets(link: serial.Serial, timeout_s: float):
    """Yields (type, data) packets and the log text read so far, until timeout."""
    buffer, log, deadline = b"", b"", time.time() + timeout_s
    while time.time() < deadline:
        chunk = link.read(256)
        log += chunk
        found, buffer = improv.parse(buffer + chunk)
        for kind, data in found:
            yield kind, data, log


def _current(link: serial.Serial) -> dict:
    """{"online": bool, "ip": str|None} from the board's Improv state (the IP comes in next_url)."""
    # Asks again every few seconds: right after a reset the board is still booting, and while it joins the network
    # it reports its saved Wi-Fi with the address 0.0.0.0.
    answered, deadline = False, time.time() + STATE_TIMEOUT_S
    while time.time() < deadline:
        link.write(improv.rpc(improv.CMD_STATE))
        online = False
        for kind, data, _ in _packets(link, STATE_RETRY_S):
            answered = True
            if kind == improv.TYPE_STATE:
                online = data[0] == improv.STATE_PROVISIONED
                if not online:
                    return {"online": False, "ip": None}
            ip = _ip_in_url(improv.result_strings(data)[1]) if kind == improv.TYPE_RESULT and online else None
            if ip:
                return {"online": True, "ip": ip}
    if answered:
        return {"online": True, "ip": None}
    raise BoardError("E_IMPROV_TIMEOUT", "La placa no responde. ¿Tiene el firmware del Estudio y el cable en «COM»?")


def status(port: str) -> dict:
    with open_port(port) as link:
        return _current(link)


def scan(port: str) -> dict:
    """Networks the board sees, plus its current state (a board already on Wi-Fi does not scan: empty list)."""
    with open_port(port) as link:
        current = _current(link)
        link.write(improv.rpc(improv.CMD_SCAN))
        networks = []
        for kind, data, _ in _packets(link, SCAN_TIMEOUT_S):
            if kind == improv.TYPE_ERROR and data[0]:
                raise BoardError(improv.ERRORS.get(data[0], "E_IMPROV_UNKNOWN"), "La placa no pudo buscar redes.")
            if kind == improv.TYPE_RESULT and improv.result_strings(data)[0] == improv.CMD_SCAN:
                values = improv.result_strings(data)[1]
                if not values:
                    return {**current, "networks": sorted(networks, key=lambda n: -n["rssi"])}
                networks.append({"ssid": values[0], "rssi": int(values[1]), "secure": values[2] == "YES"})
    raise BoardError("E_IMPROV_TIMEOUT", "La placa no responde. ¿Tiene el firmware del Estudio y el cable en «COM»?")


def wifi(port: str, ssid: str, password: str) -> str:
    with open_port(port) as link:
        link.write(improv.wifi_rpc(ssid, password))
        provisioned = False
        for kind, data, log in _packets(link, WIFI_TIMEOUT_S):
            if kind == improv.TYPE_ERROR and data[0]:
                code = improv.ERRORS.get(data[0], "E_IMPROV_UNKNOWN")
                raise BoardError(code, "La placa no pudo entrar en la red. Revisa el nombre y la clave.")
            if kind == improv.TYPE_STATE and data[0] == improv.STATE_PROVISIONED:
                provisioned = True
            urls = improv.result_strings(data)[1] if kind == improv.TYPE_RESULT else []
            ip = _ip_in_url(urls) or improv.ip_from_log(log)
            if provisioned and ip:
                return f"OK: placa en {ip}"
    raise BoardError("E_IMPROV_TIMEOUT", "La placa no confirmó la conexión en 60 s. Revisa la red y la clave.")


def _ip_in_url(urls: list) -> str | None:
    for url in urls:
        host = url.split("//")[-1].split("/")[0].split(":")[0]
        if host.count(".") == 3 and host != "0.0.0.0":  # 0.0.0.0 = still joining the network
            return host
    return None
