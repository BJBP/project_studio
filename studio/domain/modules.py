# Modules, pure rules: what a manifest (modules/<id>/module.json) must say, and which modules can be on together.
# A tab is {id, order, when?}; a block is {tab, entry (path under web/studio/), export (its create function)}.
# check_manifest(m) -> [issue]; active_order(manifests, enabled) -> (ordered ids, [issue]). Issues: {"code", ...}.
REQUIRED = ("id", "name", "version", "license")
ADD_KINDS = ("tabs", "blocks")


def check_manifest(manifest: dict) -> list:
    missing = [k for k in REQUIRED if not str(manifest.get(k, "")).strip()]
    if missing:
        return [{"code": "E_MODULE_MANIFEST", "module": manifest.get("id", "?"), "fields": ", ".join(missing)}]
    issues = []
    for kind in manifest.get("adds", {}):
        if kind not in ADD_KINDS:
            issues.append({"code": "E_MODULE_MANIFEST", "module": manifest["id"], "fields": f"adds.{kind}"})
    adds = manifest.get("adds", {})
    if any(not tab.get("id") for tab in adds.get("tabs", [])):
        issues.append({"code": "E_MODULE_MANIFEST", "module": manifest["id"], "fields": "adds.tabs[].id"})
    if any(not (b.get("tab") and b.get("entry") and b.get("export")) for b in adds.get("blocks", [])):
        issues.append({"code": "E_MODULE_MANIFEST", "module": manifest["id"], "fields": "adds.blocks[].tab/entry/export"})
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
        for need in manifests[module_id].get("requires", []):
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
    """Enabled modules that need module_id (it cannot be turned off while they are on)."""
    return sorted(m for m in enabled if module_id in manifests.get(m, {}).get("requires", []))
