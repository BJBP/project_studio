# Modules, use cases: list them with their state, turn one on or off, and install, update or uninstall one from a .zip.
# The ModuleStore port reads the manifests (included and installed), keeps which ones are on and unpacks packages.
# Raises StudioError with a code the presentation explains.
import json
from typing import Protocol

from studio.application.use_cases import StudioError
from studio.domain import modules as rules
from studio.domain import packages


class ModuleStore(Protocol):
    def manifests(self) -> dict: ...          # id -> manifest (modules/<id>/module.json)
    def enabled(self) -> set | None: ...      # None: never chosen, every module the program brings is on
    def save_enabled(self, ids: set) -> None: ...
    def open_package(self, data: bytes): ...  # a zipfile.ZipFile, or StudioError E_EXT_BAD_ZIP / E_EXT_UNSAFE_PATH
    def install(self, package, prefix: str, module_id: str) -> None: ...
    def uninstall(self, module_id: str) -> None: ...


def _enabled(store: ModuleStore) -> set:
    chosen = store.enabled()
    return set(store.manifests()) if chosen is None else chosen


def list_modules(store: ModuleStore) -> dict:
    manifests, enabled = store.manifests(), _enabled(store)
    active, issues = rules.active_order(manifests, enabled)
    for manifest in manifests.values():
        issues += rules.check_manifest(manifest)
    items = [{**{k: v for k, v in m.items() if not k.startswith("_")},  # no local paths for the page
              "enabled": m["id"] in enabled, "active": m["id"] in active} for m in manifests.values()]
    return {"modules": sorted(items, key=lambda m: (m.get("order", 99), m["id"])), "active": active, "issues": issues}


def set_enabled(store: ModuleStore, module_id: str, on: bool) -> dict:
    manifests, enabled = store.manifests(), _enabled(store)
    if module_id not in manifests:
        raise StudioError("E_MODULE_NOT_FOUND", module=module_id)
    if on:
        missing = [need for need in rules.needs(manifests[module_id]) if need not in enabled]
        if missing:
            raise StudioError("E_MODULE_REQUIRES", module=module_id, requires=", ".join(missing))
        enabled.add(module_id)
    else:
        users = rules.required_by(manifests, enabled, module_id)
        if users:
            raise StudioError("E_MODULE_REQUIRED_BY", module=module_id, users=", ".join(users))
        enabled.discard(module_id)
    store.save_enabled(enabled)
    return list_modules(store)


def _read_package(store: ModuleStore, data: bytes):
    """(open zip, folder prefix inside it, manifest) after every check; raises StudioError on the first problem."""
    package = store.open_package(data)
    entries = [(i.filename, i.file_size, i.is_dir()) for i in package.infolist()]
    prefix, issues = packages.check_entries(entries, len(data))
    if issues:
        raise StudioError(**issues[0])
    names = {n.replace("\\", "/"): n for n in package.namelist()}  # some zip tools write \ in names
    try:
        manifest = json.loads(package.read(names[prefix + packages.MANIFEST]))
    except (ValueError, KeyError):
        raise StudioError("E_EXT_NO_MANIFEST") from None
    issues = rules.check_manifest(manifest) if isinstance(manifest, dict) else [{"code": "E_EXT_NO_MANIFEST"}]
    if issues:
        raise StudioError(**issues[0])
    if manifest.get("adds", {}).get("connector") and prefix + "translate.py" not in names:
        raise StudioError("E_EXT_MISSING_FILE", file="translate.py")
    return package, prefix, manifest


def inspect_package(store: ModuleStore, data: bytes) -> dict:
    """What the zip would install, without writing anything."""
    _package, _prefix, manifest = _read_package(store, data)
    current = store.manifests().get(manifest["id"])
    if current and current.get("origin") == "included":
        raise StudioError("E_EXT_INCLUDED", module=manifest["id"])
    parent = manifest.get("parent")
    if parent and parent not in store.manifests():
        raise StudioError("E_MODULE_REQUIRES", module=manifest["id"], requires=parent)
    return packages.summary(manifest, current, False)


def install_package(store: ModuleStore, data: bytes) -> dict:
    """Installs or updates the module in the zip; it is on afterwards."""
    inspect_package(store, data)
    package, prefix, manifest = _read_package(store, data)
    store.install(package, prefix, manifest["id"])
    enabled = _enabled(store) | {manifest["id"]}
    store.save_enabled(enabled)
    return list_modules(store)


def uninstall_module(store: ModuleStore, module_id: str) -> dict:
    manifests = store.manifests()
    if module_id not in manifests:
        raise StudioError("E_MODULE_NOT_FOUND", module=module_id)
    if manifests[module_id].get("origin") != "installed":
        raise StudioError("E_EXT_INCLUDED", module=module_id)
    users = rules.required_by(manifests, set(manifests), module_id)  # submodules block it even when off
    if users:
        raise StudioError("E_MODULE_REQUIRED_BY", module=module_id, users=", ".join(users))
    store.uninstall(module_id)
    store.save_enabled(_enabled(store) - {module_id})
    return list_modules(store)
