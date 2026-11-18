# /// script
# requires-python = ">=3.11"
# dependencies = ["websockets>=12"]
# ///
# End-to-end check of a spoken order reaching the device: sends a typed order through the Home Assistant voice
# pipeline and waits for the command on MQTT (what the ESP32, real or virtual, receives). Needs the Demo page
# opened once, so the devices are announced.
# Usage: uv run tests/e2e/device_control.py ["enciende el foco"] [studio/circuito_maestro/foco/set]   Exit 0 = ON sent.
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import websockets

HA_URL = os.environ.get("HA_URL", "http://127.0.0.1:8123")
MQTT_CONTAINER = os.environ.get("MQTT_CONTAINER", "domotica-voz-mosquitto-1")
SECRETS = Path.home() / ".agents" / "secrets" / "project_studio" / "ha.json"
WAIT_SECONDS = 30


async def run_text(token: str, text: str) -> str:
    async with websockets.connect(HA_URL.replace("http", "ws", 1) + "/api/websocket") as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        await ws.recv()
        await ws.send(json.dumps({"id": 1, "type": "assist_pipeline/run", "start_stage": "intent",
                                  "end_stage": "intent", "input": {"text": text}}))
        while True:
            event = json.loads(await ws.recv()).get("event", {})
            if event.get("type") == "intent-end":
                return event["data"]["intent_output"]["response"]["speech"]["plain"]["speech"]
            if event.get("type") in ("error", "run-end"):
                return f"E_ASSIST: {event.get('data')}"


def main() -> int:
    order = sys.argv[1] if len(sys.argv) > 1 else "enciende el foco"
    topic = sys.argv[2] if len(sys.argv) > 2 else "studio/circuito_maestro/foco/set"
    token = json.loads(SECRETS.read_text(encoding="utf-8"))["token"]
    listener = subprocess.Popen(["docker", "exec", MQTT_CONTAINER, "mosquitto_sub", "-t", topic, "-C", "1",
                                 "-W", str(WAIT_SECONDS)], stdout=subprocess.PIPE, text=True)
    answer = asyncio.run(run_text(token, order))
    received = listener.communicate(timeout=WAIT_SECONDS + 5)[0].strip()
    print(json.dumps({"order": order, "answer": answer, "mqtt": received}, ensure_ascii=False))
    return 0 if received == "ON" else 1


if __name__ == "__main__":
    sys.exit(main())
