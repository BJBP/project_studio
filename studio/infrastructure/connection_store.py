# External connections on disk: the connectors (connectors/<type>/connector.json in the program folder, or installed
# in the data folder's connectors/, where private ones go), the user's
# connections (<data>/connections.json) and the live status the background process writes
# (<data>/connections_status.json). Implements studio.application.connections.ConnectionStore.
import json
from pathlib import Path

CONNECTIONS_FILE = "connections.json"
STATUS_FILE = "connections_status.json"


def _read(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


class JsonConnectionStore:
    def __init__(self, program_dir: Path, data_dir: Path):
        self.connector_dirs = [Path(program_dir) / "connectors", Path(data_dir) / "connectors"]
        self.file = Path(data_dir) / CONNECTIONS_FILE
        self.status_file = Path(data_dir) / STATUS_FILE

    def connectors(self) -> dict:
        found = {}
        for path in (p for folder in self.connector_dirs for p in sorted(folder.glob("*/connector.json"))):
            connector = _read(path, None)
            if isinstance(connector, dict):  # a broken manifest is skipped, not fatal
                found[connector.get("type", path.parent.name)] = {**connector, "_dir": str(path.parent)}
        return found

    def load(self) -> list:
        return _read(self.file, {}).get("connections", [])

    def save(self, connections: list) -> None:
        self.file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.file.with_suffix(".tmp")
        tmp.write_text(json.dumps({"connections": connections}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(self.file)

    def status(self) -> dict:
        return _read(self.status_file, {})
