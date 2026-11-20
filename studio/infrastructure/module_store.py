# Modules on disk: the manifests the program brings (modules/<id>/module.json) and which ones are on, in the user's
# data folder (modules.json; missing = every module on). Implements studio.application.modules.ModuleStore.
import json
from pathlib import Path


class JsonModuleStore:
    def __init__(self, program_dir: Path, data_dir: Path):
        self.modules_dir = Path(program_dir) / "modules"
        self.state_file = Path(data_dir) / "modules.json"

    def manifests(self) -> dict:
        found = {}
        for path in sorted(self.modules_dir.glob("*/module.json")):
            manifest = json.loads(path.read_text(encoding="utf-8"))
            found[manifest.get("id", path.parent.name)] = manifest
        return found

    def enabled(self) -> set | None:
        if not self.state_file.exists():
            return None
        return set(json.loads(self.state_file.read_text(encoding="utf-8")).get("enabled", []))

    def save_enabled(self, ids: set) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps({"enabled": sorted(ids)}, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.state_file)
