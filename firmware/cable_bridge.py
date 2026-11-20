# /// script
# requires-python = ">=3.11"
# dependencies = ["pyserial>=3.5", "paho-mqtt>=2", "httpx>=0.27", "websockets>=12"]
# ///
# Cable mode: keeps the board in Home Assistant over the USB cable while it has no Wi-Fi. Reads the board's "@" lines
# on its «COM» port; with no Wi-Fi it announces "<device> (cable)" over MQTT and passes the orders back as "@set";
# when the Wi-Fi returns it takes that stand-in out (the real board answers again). While on cable, the board's
# Wi-Fi entities are hidden from the voice assistant, so «apaga el ventilador» reaches the cable. Runs until stopped.
# Usage: uv run firmware/cable_bridge.py --port COM4 [--device circuito_maestro] [--project domotica-voz]
#        uv run firmware/cable_bridge.py --restore [--device ...]: takes the stand-in out and shows the Wi-Fi entities
#        again (the Studio runs it after stopping the bridge, which is killed without a chance to clean up).
# Prints one line per change: "CABLE: ...", "WIFI: ...", or "<CODE>: <what to do>" (exit 1).
import argparse
import json
import os
import sys
import time
from pathlib import Path

import paho.mqtt.client as mqtt
import serial

import cable
from board_link import BoardError, open_port

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "web" / "demos" / "voice" / "data" / "devices.example.json"
DATA = Path(os.environ.get("STUDIO_DATA", ROOT.parent / "project_studio_data"))
STACK_ENV = ROOT / "stack" / "domotica-voz" / ".env"
SECRETS = Path(os.environ.get("STUDIO_SECRETS", Path.home() / ".agents" / "secrets" / "project_studio"))
sys.path.insert(0, str(ROOT / "stack" / "domotica-voz" / "setup"))
GET_EVERY_S = 30
DISCOVERY_WAIT_S = 3  # Home Assistant creates the stand-in a moment after the announcement  # asks for every state again now and then (a missed line heals itself)


def load_device(device_id: str, project: str) -> tuple[dict, dict, str]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    device = next((d for d in catalog["devices"] if d["id"] == device_id), None)
    if not device:
        raise BoardError("E_UNKNOWN_DEVICE", f"No hay aparato «{device_id}» en el catálogo.")
    state_file = DATA / "projects" / project / "state.json"
    names = json.loads(state_file.read_text(encoding="utf-8")).get("names", {}) if state_file.exists() else {}
    return device, names.get(device_id, {}), catalog["base_topic"]


def stack_port(name: str, default: str) -> str:
    """A port from the environment (the launcher sets it), else from the voice stack's .env, else the default."""
    if name in os.environ:
        return os.environ[name]
    lines = STACK_ENV.read_text(encoding="utf-8").splitlines() if STACK_ENV.exists() else []
    return next((line.split("=", 1)[1].strip() for line in lines if line.startswith(f"{name}=")), default)


def show_to_voice(device: dict, names: dict, on_cable: bool) -> None:
    """Shows the assistant the set of entities that answers now (cable or Wi-Fi) and hides the other one."""
    from ha_client import HaClient, HaError
    try:
        token = json.loads((SECRETS / "ha.json").read_text(encoding="utf-8"))["token"]
        url = os.environ.get("HA_URL", f"http://127.0.0.1:{stack_port('HA_PORT', '8123')}")
        expose = {"type": "homeassistant/expose_entity", "assistants": ["conversation"]}
        commands = [{**expose, "entity_ids": cable.entity_ids(device, via_cable=False), "should_expose": not on_cable}]
        if on_cable:
            time.sleep(DISCOVERY_WAIT_S)
            commands.append({**expose, "entity_ids": cable.entity_ids(device, via_cable=True), "should_expose": True})
            commands += [{"type": "config/entity_registry/update", "entity_id": entity_id, "aliases": [alias]}
                         for entity_id, alias in cable.voice_aliases(device, names)]
        HaClient(url, token).ws(*commands)
    except (HaError, OSError, KeyError, json.JSONDecodeError) as err:
        print(f"AVISO E_HA_EXPOSE: la voz puede no llegar por el cable ({err})", flush=True)


def connect_mqtt(base: str, device: dict, orders: list) -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{device['id']}_cable")
    client.will_set(cable.availability_topic(base, device), "offline", retain=True)
    client.on_message = lambda _c, _u, msg: orders.append((msg.topic, msg.payload.decode("utf-8", errors="replace")))
    try:
        client.connect(os.environ.get("MQTT_HOST", "127.0.0.1"), int(stack_port("MQTT_PORT", "1883")))
    except OSError as err:
        raise BoardError("E_MQTT_DOWN", "No responde MQTT: arranca el stack de voz.") from err
    client.subscribe(f"{base}/{device['id']}_cable/+/set")
    client.loop_start()
    return client


def announce(client, base: str, device: dict, names: dict, on_cable: bool) -> None:
    for topic, payload in cable.discovery(base, device, names) if on_cable else cable.removal(device):
        client.publish(topic, payload, retain=True)
    client.publish(cable.availability_topic(base, device), "online" if on_cable else "offline", retain=True)
    show_to_voice(device, names, on_cable)
    print("CABLE: la placa sigue en Home Assistant por el cable" if on_cable else "WIFI: la placa usa su Wi-Fi", flush=True)


def run(port: str, device_id: str, project: str) -> None:
    device, names, base = load_device(device_id, project)
    orders, on_cable, asked = [], None, 0.0
    client = connect_mqtt(base, device, orders)
    with open_port(port) as link:
        while True:
            if time.time() - asked > GET_EVERY_S:
                link.write(cable.GET_LINE)
                asked = time.time()
            while orders:
                if line := cable.command_line(base, device, *orders.pop(0)):
                    link.write(line)
            found = cable.parse(link.readline())
            if found and found["kind"] == "wifi" and on_cable != (not found["online"]):
                on_cable = not found["online"]
                announce(client, base, device, names, on_cable)
                asked = 0.0  # fresh states for the stand-in
            elif found and found["kind"] == "state" and on_cable:
                if message := cable.state_message(base, device, found):
                    client.publish(*message, retain=True)


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(prog="cable_bridge.py")
    parser.add_argument("--port")
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--device", default="circuito_maestro")
    parser.add_argument("--project", default="domotica-voz")
    args = parser.parse_args(argv)
    try:
        if args.restore:
            device, names, base = load_device(args.device, args.project)
            client = connect_mqtt(base, device, [])
            announce(client, base, device, names, on_cable=False)
            client.loop_stop()
            client.disconnect()
            return 0
        if not args.port:
            raise BoardError("E_NO_PORT", "Falta --port (mira los puertos con: board.py ports).")
        run(args.port, args.device, args.project)
    except BoardError as err:
        print(err, flush=True)
        return 1
    except serial.SerialException:
        print("E_PORT_LOST: se perdió la placa (¿cable suelto?). Conéctala y vuelve a activar el modo cable.", flush=True)
        return 1
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
