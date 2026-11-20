# External connections on their own: while the Studio runs, connectors/run.py runs whenever some connection is on
# (<data>/connections.json) and stops when none is. The process itself rereads the file when it changes.
# start_watch(data_dir) starts the background check; should_run(connections) is the rule.
import json
import shutil
import threading
import time
from pathlib import Path

import serve_jobs

JOB = "connections"
RUNNER = Path(__file__).resolve().parent / "connectors" / "run.py"
EVERY_S = 10


def should_run(connections: list) -> bool:
    return any(c.get("enabled", True) and c.get("devices") for c in connections)


def tick(data_dir: Path) -> None:
    path = Path(data_dir) / "connections.json"
    connections = json.loads(path.read_text(encoding="utf-8")).get("connections", []) if path.exists() else []
    running = serve_jobs.status(JOB)["state"] == "running"
    if should_run(connections) and not running:
        serve_jobs.start(JOB, [shutil.which("uv") or "uv", "run", "--quiet", str(RUNNER)], "Conectando…", live=True)
    elif running and not should_run(connections):
        serve_jobs.stop(JOB)


def start_watch(data_dir: Path) -> None:
    def loop():
        while True:
            try:
                tick(data_dir)
            except (OSError, ValueError) as err:  # a bad file must not stop the Studio; the next check tries again
                print(f"AVISO E_CONN_WATCH: {err}", flush=True)
            time.sleep(EVERY_S)
    threading.Thread(target=loop, daemon=True).start()
