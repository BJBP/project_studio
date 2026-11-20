# Module packages (.zip), pure: checks the list of files before anything is written. entries = [(name, size, is_dir)].
# check_entries(entries, zip_size) -> (prefix of the module folder inside the zip, [issue]). The prefix is "" when
# module.json is at the root, or "<folder>/" when the zip holds one folder. Issues: {"code": "E_EXT_*", ...}.
MAX_ZIP_BYTES = 2 * 1024 * 1024
MAX_UNPACKED_BYTES = 5 * 1024 * 1024
MAX_FILES = 200
MANIFEST = "module.json"


def _unsafe(name: str) -> bool:
    parts = name.replace("\\", "/").split("/")
    return name.startswith(("/", "\\")) or ":" in parts[0] or ".." in parts


def check_entries(entries: list, zip_size: int) -> tuple[str, list]:
    entries = [(name.replace("\\", "/"), size, is_dir) for name, size, is_dir in entries]  # some zip tools use \
    if zip_size > MAX_ZIP_BYTES:
        return "", [{"code": "E_EXT_TOO_BIG", "limit": MAX_ZIP_BYTES // (1024 * 1024)}]
    files = [(name, size) for name, size, is_dir in entries if not is_dir]
    if len(files) > MAX_FILES or sum(size for _, size in files) > MAX_UNPACKED_BYTES:
        return "", [{"code": "E_EXT_TOO_BIG", "limit": MAX_UNPACKED_BYTES // (1024 * 1024)}]
    if any(_unsafe(name) for name, _, _ in entries):
        return "", [{"code": "E_EXT_UNSAFE_PATH"}]
    manifests = [name for name, _ in files if name.replace("\\", "/").split("/")[-1] == MANIFEST
                 and name.replace("\\", "/").count("/") <= 1]
    if len(manifests) != 1:
        return "", [{"code": "E_EXT_NO_MANIFEST" if not manifests else "E_EXT_MANY_MANIFESTS"}]
    prefix = manifests[0][: -len(MANIFEST)]
    if prefix and any(not name.startswith(prefix) for name, _ in files):
        return "", [{"code": "E_EXT_LAYOUT"}]
    return prefix, []


def summary(manifest: dict, installed: dict | None, included: bool) -> dict:
    """What the person sees before installing: the manifest, what it adds and what it replaces."""
    adds = manifest.get("adds", {})
    added = [f"tab:{t['id']}" for t in adds.get("tabs", [])] + [f"block:{b['export']}" for b in adds.get("blocks", [])]
    if adds.get("connector"):
        added.append(f"connector:{adds['connector']['type']}")
    return {"id": manifest["id"], "name": manifest["name"], "version": manifest["version"],
            "license": manifest["license"], "icon": manifest.get("icon"), "description": manifest.get("description", ""),
            "parent": manifest.get("parent"), "adds": added, "replaces": (installed or {}).get("version"),
            "included": included}
