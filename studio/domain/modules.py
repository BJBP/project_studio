# Modules, pure rules: what a manifest (module.json) must say, and which modules can be on together.
# A tab is {id, order, when?}; a block is {tab, entry (path under web/studio/), export (its create function)};
# a connector is {type, transport, options} (a submodule of "conexiones" with its translate.py).
# "parent": a submodule counts its parent as a requirement. Issues: {"code", ...}.
# check_manifest(m) -> [issue]; active_order(manifests, enabled) -> (ordered ids, [issue]); needs(m) -> [id].
import re

REQUIRED = ("id", "name", "version", "license")
ADD_KINDS = ("tabs", "blocks", "connector")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def needs(manifest: dict) -> list:
    """What a module needs on: its requirements and, for a submodule, its parent."""
    parent = [manifest["parent"]] if manifest.get("parent") else []
    return list(dict.fromkeys(list(manifest.get("requires", [])) + parent))


def check_manifest(manifest: dict) -> list:
    missing = [k for k in REQUIRED if not str(manifest.get(k, "")).strip()]
    if missing:
        return [{"code": "E_MODULE_MANIFEST", "module": manifest.get("id", "?"), "fields": ", ".join(missing)}]
    issues = [] if ID_RE.match(str(manifest["id"])) else [{"code": "E_MODULE_MANIFEST", "module": manifest["id"], "fields": "id"}]
    for kind in manifest.get("adds", {}):
        if kind not in ADD_KINDS:
            issues.append({"code": "E_MODULE_MANIFEST", "module": manifest["id"], "fields": f"adds.{kind}"})
    adds = manifest.get("adds", {})
    if any(not tab.get("id") for tab in adds.get("tabs", [])):
        issues.append({"code": "E_MODULE_MANIFEST", "module": manifest["id"], "fields": "adds.tabs[].id"})
    if any(not (b.get("tab") and b.get("entry") and b.get("export")) for b in adds.get("blocks", [])):
        issues.append({"code": "E_MODULE_MANIFEST", "module": manifest["id"], "fields": "adds.blocks[].tab/entry/export"})
    connector = adds.get("connector")
    if connector is not None and not (isinstance(connector, dict) and connector.get("type") and connector.get("transport")):
        issues.append({"code": "E_MODULE_MANIFEST", "module": manifest["id"], "fields": "adds.connector.type/transport"})
    return issues


def active_order(manifests: dict, enabled: set) -> tuple[list, list]:
    """Enabled modules whose requirements are on too, dependencies first. A module with a missing or disabled
    requirement, or in a cycle, is left out with an issue."""
    order, issues, state = [], [], {}

    def visit(module_id: str, path: tuple) -> bool:
        if state.get(module_id) == "done":
            return True
        if module_id in path:
            issues.append({"code": "E_MODULE_CYCLE", "module": module_id})
            return False
        for need in needs(manifests[module_id]):
            if need not in manifests or need not in enabled:
                issues.append({"code": "E_MODULE_REQUIRES", "module": module_id, "requires": need})
                return False
            if not visit(need, path + (module_id,)):
                return False
        state[module_id] = "done"
        order.append(module_id)
        return True

    for module_id in sorted(enabled & set(manifests)):
        visit(module_id, ())
    return order, issues


def required_by(manifests: dict, enabled: set, module_id: str) -> list:
    """Enabled modules that need module_id, its submodules included (it cannot be turned off while they are on)."""
    return sorted(m for m in enabled if module_id in needs(manifests.get(m, {})))
