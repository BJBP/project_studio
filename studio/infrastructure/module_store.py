# Modules on disk: those the program brings (modules/<id>/module.json, "included") and those the person installed from a
# .zip (<data>/modules/<id>/, "installed"), plus which ones are on (<data>/modules.json; missing = all on).
# Implements studio.application.modules.ModuleStore; reads zips without writing, writes only into <data>/modules/.
import io
import json
import shutil
import stat
import zipfile
from pathlib import Path

from studio.application.use_cases import StudioError


def _manifests_in(folder: Path, origin: str) -> dict:
    found = {}
    for path in sorted(folder.glob("*/module.json")):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue  # a broken installed module is skipped, not fatal
        if isinstance(manifest, dict):
            found[manifest.get("id", path.parent.name)] = {**manifest, "origin": origin, "_dir": str(path.parent)}
    return found


class JsonModuleStore:
    def __init__(self, program_dir: Path, data_dir: Path):
        self.modules_dir = Path(program_dir) / "modules"
        self.installed_dir = Path(data_dir) / "modules"
        self.state_file = Path(data_dir) / "modules.json"

    def manifests(self) -> dict:
        included = _manifests_in(self.modules_dir, "included")
        installed = {k: v for k, v in _manifests_in(self.installed_dir, "installed").items() if k not in included}
        return {**included, **installed}

    def enabled(self) -> set | None:
        if not self.state_file.exists():
            return None
        return set(json.loads(self.state_file.read_text(encoding="utf-8")).get("enabled", []))

    def save_enabled(self, ids: set) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps({"enabled": sorted(ids)}, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.state_file)

    def open_package(self, data: bytes) -> zipfile.ZipFile:
        try:
            package = zipfile.ZipFile(io.BytesIO(data))
        except (zipfile.BadZipFile, ValueError):
            raise StudioError("E_EXT_BAD_ZIP") from None
        if any(stat.S_ISLNK(info.external_attr >> 16) for info in package.infolist()):
            raise StudioError("E_EXT_UNSAFE_PATH")  # links could point outside the module folder
        return package

    def install(self, package: zipfile.ZipFile, prefix: str, module_id: str) -> None:
        """Unpacks the module folder into <data>/modules/<id>/, replacing an older version only once it is complete."""
        target, tmp = self.installed_dir / module_id, self.installed_dir / f".{module_id}.tmp"
        shutil.rmtree(tmp, ignore_errors=True)
        for info in package.infolist():
            if info.is_dir():
                continue
            dest = tmp / info.filename.replace("\\", "/")[len(prefix):]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(package.read(info))
        shutil.rmtree(target, ignore_errors=True)
        tmp.replace(target)

    def uninstall(self, module_id: str) -> None:
        target = self.installed_dir / module_id
        if target.parent == self.installed_dir and target.is_dir():
            shutil.rmtree(target)
