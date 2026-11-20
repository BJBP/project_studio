# One running connection over MQTT: its client, its connector's translator (translate.py in the connector's folder)
# and its live status. Link(conn, folder, loop, orders, status); send(entity_id, state) publishes; orders arrive in the asyncio queue
# as (link, topic, payload). In Docker, 127.0.0.1 means the computer, reached as host.docker.internal.
import importlib.util
import time
from pathlib import Path

import paho.mqtt.client as mqtt

IN_DOCKER = Path("/.dockerenv").exists()


def translator(folder: str):
    spec = importlib.util.spec_from_file_location(f"connector_{Path(folder).name}", Path(folder) / "translate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Link:
    def __init__(self, conn: dict, folder: str, loop, orders, status: dict):
        self.conn, self.code = conn, translator(folder)
        self.status = status.setdefault(conn["id"], {})
        options = conn["options"]
        host = "host.docker.internal" if IN_DOCKER and options["host"] in ("127.0.0.1", "localhost") else options["host"]
        self.where = f"{host}:{options['port']}"
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"studio-{conn['id']}")
        self.client.on_connect = lambda c, u, f, rc, p: self._connected(rc)
        self.client.on_disconnect = lambda c, u, f, rc, p: self._set("error", f"E_CONN_DOWN: {self.where}")
        self.client.on_message = lambda c, u, m: loop.call_soon_threadsafe(orders.put_nowait, (self, m.topic, m.payload))
        self._set("connecting", self.where)
        self.client.connect_async(host, int(options["port"]))
        self.client.loop_start()

    def _set(self, state: str, message: str = "") -> None:
        self.status.update(state=state, message=message)

    def _connected(self, rc) -> None:
        if rc.is_failure:
            return self._set("error", f"E_CONN_REFUSED: {self.where} ({rc})")
        for topic in self.code.subscriptions(self.conn["options"]):
            self.client.subscribe(topic)
        self._set("connected", self.where)

    def send(self, entity_id: str, state: dict | None) -> None:
        for device in (d for d in self.conn["devices"] if d["entity_id"] == entity_id):
            for topic, payload in self.code.outgoing(self.conn["options"], device, state):
                self.client.publish(topic, payload, retain=topic.endswith("/status"))
            self.status["sent_at"] = time.time()

    def close(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
