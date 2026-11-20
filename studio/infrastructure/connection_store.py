# External connections on disk: the connectors (the active submodules of "conexiones" that add a connector, with their
# translate.py), the user's connections (<data>/connections.json) and the live status the background process writes
# (<data>/connections_status.json). Implements studio.application.connections.ConnectionStore.
import json
from pathlib import Path

from studio.domain.modules import active_order
from studio.infrastructure.module_store import JsonModuleStore

CONNECTIONS_FILE = "connections.json"
STATUS_FILE = "connections_status.json"


def _read(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


class JsonConnectionStore:
    def __init__(self, program_dir: Path, data_dir: Path):
        self.modules = JsonModuleStore(program_dir, data_dir)
        self.file = Path(data_dir) / CONNECTIONS_FILE
        self.status_file = Path(data_dir) / STATUS_FILE

    def connectors(self) -> dict:
        """{type: connector} from the active modules that add one; "_dir" is the module folder (for translate.py)."""
        manifests = self.modules.manifests()
        chosen = self.modules.enabled()
        active, _issues = active_order(manifests, set(manifests) if chosen is None else chosen)
        found = {}
        for module_id in active:
            manifest = manifests[module_id]
            connector = manifest.get("adds", {}).get("connector")
            if connector:
                found[connector["type"]] = {**connector, "name": manifest["name"], "icon": manifest.get("icon"),
                                            "version": manifest["version"], "license": manifest["license"],
                                            "description": manifest.get("description", ""), "_dir": manifest["_dir"]}
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
