# Modules, use cases: list them with their state, turn one on or off. The ModuleStore port reads the manifests and
# keeps which ones are on (in the user's data folder). Raises StudioError with a code the presentation explains.
from typing import Protocol

from studio.application.use_cases import StudioError
from studio.domain import modules as rules


class ModuleStore(Protocol):
    def manifests(self) -> dict: ...          # id -> manifest (modules/<id>/module.json)
    def enabled(self) -> set | None: ...      # None: never chosen, every module the program brings is on
    def save_enabled(self, ids: set) -> None: ...


def _enabled(store: ModuleStore) -> set:
    chosen = store.enabled()
    return set(store.manifests()) if chosen is None else chosen


def list_modules(store: ModuleStore) -> dict:
    manifests, enabled = store.manifests(), _enabled(store)
    active, issues = rules.active_order(manifests, enabled)
    for manifest in manifests.values():
        issues += rules.check_manifest(manifest)
    items = [{**m, "enabled": m["id"] in enabled, "active": m["id"] in active} for m in manifests.values()]
    return {"modules": sorted(items, key=lambda m: (m.get("order", 99), m["id"])), "active": active, "issues": issues}


def set_enabled(store: ModuleStore, module_id: str, on: bool) -> dict:
    manifests, enabled = store.manifests(), _enabled(store)
    if module_id not in manifests:
        raise StudioError("E_MODULE_NOT_FOUND", module=module_id)
    if on:
        missing = [need for need in manifests[module_id].get("requires", []) if need not in enabled]
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
