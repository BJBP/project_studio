# /// script
# requires-python = ">=3.11"
# dependencies = ["paho-mqtt>=2", "websockets>=12"]
# ///
# External connections, running: follows Home Assistant and sends each shared device's state to its connections
# (<data>/connections.json); orders from a platform become Home Assistant calls. Rereads the file when it changes and
# writes <data>/connections_status.json. Only one copy runs (connections.lock with a heartbeat); others exit 0.
# Usage: uv run connectors/run.py   (the Studio starts it). Prints "<CODE>: <what to do>" lines on problems.
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import websockets

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "stack" / "domotica-voz" / "setup")]
from connectors.link import Link  # noqa: E402
from local_access import ha_access  # noqa: E402
from studio.domain.connections import with_defaults  # noqa: E402
from studio.infrastructure.connection_store import JsonConnectionStore  # noqa: E402
from studio.presentation.wiring import default_data_dir  # noqa: E402

DATA = default_data_dir()
LOCK = DATA / "connections.lock"
BEAT_S, STALE_S = 5, 30


def took_lock() -> bool:
    """True if no other copy is alive; then this one owns the lock (and keeps it with beat())."""
    try:
        other = json.loads(LOCK.read_text(encoding="utf-8"))
        if other["pid"] != os.getpid() and time.time() - other["beat"] < STALE_S:
            return False
    except (OSError, ValueError, KeyError):
        pass
    beat()
    return True


def beat() -> None:
    LOCK.write_text(json.dumps({"pid": os.getpid(), "beat": time.time()}), encoding="utf-8")


def enabled_connections(store: JsonConnectionStore) -> list:
    """[(connection with defaults, its connector's folder)] for the connections that are on."""
    found = store.connectors()
    return [(with_defaults(c, found[c["type"]]), found[c["type"]]["_dir"]) for c in store.load()
            if c.get("enabled") and c.get("type") in found]


def changes(store: JsonConnectionStore) -> tuple:
    """When the connections and the module choices were last written (installing or turning one on writes it)."""
    return tuple(path.stat().st_mtime if path.exists() else 0 for path in (store.file, store.modules.state_file))


def write_status(store: JsonConnectionStore, status: dict) -> None:
    tmp = store.status_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(status, indent=2), encoding="utf-8")
    tmp.replace(store.status_file)


async def follow(store: JsonConnectionStore) -> None:
    """One pass: connect everything, then relay until the connections or the modules change (returns: a module was
    installed, turned on or off) or Home Assistant drops."""
    loop, orders, status = asyncio.get_running_loop(), asyncio.Queue(), {}
    stamp = changes(store)
    links = [Link(conn, folder, loop, orders, status) for conn, folder in enabled_connections(store)]
    url, token = ha_access()
    try:
        async with websockets.connect(url.replace("http", "ws", 1) + "/api/websocket", max_size=None) as sock:
            await sock.recv()
            await sock.send(json.dumps({"type": "auth", "access_token": token}))
            if json.loads(await sock.recv()).get("type") != "auth_ok":
                raise SystemExit("E_HA_AUTH: el token de Home Assistant no vale.")
            await sock.send(json.dumps({"id": 1, "type": "get_states"}))
            await sock.send(json.dumps({"id": 2, "type": "subscribe_events", "event_type": "state_changed"}))
            next_id = 3

            async def relay_orders():
                nonlocal next_id
                while True:
                    link, topic, payload = await orders.get()
                    call = link.code.incoming(link.conn["options"], link.conn["devices"], topic, payload)
                    if call:
                        await sock.send(json.dumps({"id": next_id, "type": "call_service", "domain": call["domain"],
                                                    "service": call["service"], "target": {"entity_id": call["entity_id"]}}))
                        next_id += 1

            async def keep_alive():
                while changes(store) == stamp:
                    beat()
                    write_status(store, status)
                    await asyncio.sleep(BEAT_S)

            async def read_home_assistant():
                async for raw in sock:
                    message = json.loads(raw)
                    if message.get("id") == 1 and message.get("type") == "result":
                        for state in message.get("result") or []:
                            for link in links:
                                link.send(state["entity_id"], state)
                    elif message.get("type") == "event":
                        data = message["event"]["data"]
                        for link in links:
                            link.send(data["entity_id"], data.get("new_state"))

            tasks = [asyncio.create_task(t()) for t in (relay_orders, keep_alive, read_home_assistant)]
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in tasks:
                task.cancel()
    finally:
        for link in links:
            link.close()


def main() -> None:
    if not took_lock():
        print("CONEXIONES: ya hay otro proceso a cargo; este se cierra.", flush=True)
        return
    store = JsonConnectionStore(ROOT, DATA)
    while True:
        try:
            asyncio.run(follow(store))
            print("CONEXIONES: configuración cambiada, se vuelve a conectar.", flush=True)
        except (OSError, websockets.WebSocketException, KeyError, ValueError) as err:
            print(f"E_CONN_HA: no se llega a Home Assistant ({err}); se reintenta.", flush=True)
            time.sleep(BEAT_S)


if __name__ == "__main__":
    main()
