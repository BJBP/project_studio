# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27", "websockets>=12"]
# ///
# Names the catalog devices in Home Assistant so the voice can tell the real board from its virtual twin.
# With a real board: real "<name>" in the project's area (switch.<device>_<key>), virtual "<name> virtual" in the
# area "Demo" (switch.<device>_virtual_<key>). Without one, the virtual takes the plain name. <name> is the one the
# user chose in the Studio (state.json "names"), else the catalog's. Usage: uv run device_names.py [project]
# Exit 0 = "OK: n cambios"; otherwise "<CODE>: <what to do>".
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / "web" / "demos" / "voice" / "data" / "devices.example.json"
DEMO_AREA = "Demo"
VIRTUAL_MAKER = "Project Studio"  # manufacturer the virtual devices announce (discovery.js)


def _changes(entry: dict, entity_id: str, name: str) -> dict | None:
    changes = {} if entry.get("name") == name else {"name": name}
    if set(entry.get("aliases") or []) != {name}:
        changes["aliases"] = [name]
    if entry["entity_id"] != entity_id:
        changes["new_entity_id"] = entity_id
    return changes or None


def _find_devices(device: dict, devices: list) -> tuple:
    """(real board, virtual twin) registry entries for one catalog device; either may be None."""
    board = next((d for d in devices if d.get("name") == device["name"] and d.get("manufacturer") != VIRTUAL_MAKER), None)
    twin = next((d for d in devices if d.get("manufacturer") == VIRTUAL_MAKER
                 and any(i[-1] == device["id"] for i in d.get("identifiers", []))), None)
    return board, twin


def plan(catalog: dict, names: dict, entities: list, devices: list) -> dict:
    """{"entities": [(entity_id, changes)] virtual first, "areas": {device_id: area}}. Pure: no Home Assistant."""
    virtual, real, areas = [], [], {}
    for device in catalog.get("devices", []):
        board, twin = _find_devices(device, devices)
        if board:
            areas[board["id"]] = device.get("area", "")
        if twin:
            areas[twin["id"]] = DEMO_AREA if board else device.get("area", "")
        for item in device.get("entities", []):
            domain, key = item["component"], item["key"]
            chosen = names.get(device["id"], {}).get(key) or item["name"]
            mine = board and next((e for e in entities if e.get("device_id") == board["id"]
                                   and e.get("original_name") == item["name"] and e["entity_id"].startswith(f"{domain}.")), None)
            ghost = next((e for e in entities if e.get("platform") == "mqtt" and e.get("unique_id") == f"{device['id']}_{key}"), None)
            if ghost:
                target = (f"{domain}.{device['id']}_virtual_{key}", f"{chosen} virtual") if mine \
                    else (f"{domain}.{device['id']}_{key}", chosen)
                if changes := _changes(ghost, *target):
                    virtual.append((ghost["entity_id"], changes))
            if mine and (changes := _changes(mine, f"{domain}.{device['id']}_{key}", chosen)):
                real.append((mine["entity_id"], changes))
    return {"entities": virtual + real, "areas": areas}  # virtual first: it frees the plain id for the board


def _apply(client, steps: dict, devices: list) -> int:
    area_ids = {a["name"]: a["area_id"] for a in client.ws({"type": "config/area_registry/list"})[0]}
    current = {d["id"]: d.get("area_id") for d in devices}
    count = 0
    for device_id, area in steps["areas"].items():
        if not area:
            continue
        if area not in area_ids:
            area_ids[area] = client.ws({"type": "config/area_registry/create", "name": area})[0]["area_id"]
        if current.get(device_id) != area_ids[area]:
            client.ws({"type": "config/device_registry/update", "device_id": device_id, "area_id": area_ids[area]})
            count += 1
    for entity_id, changes in steps["entities"]:
        client.ws({"type": "config/entity_registry/update", "entity_id": entity_id, **changes})
        count += 1
    return count


def main(argv: list) -> int:
    from ha_client import HaClient, HaError
    secrets = Path(os.environ.get("STUDIO_SECRETS", Path.home() / ".agents" / "secrets" / "project_studio"))
    data = Path(os.environ.get("STUDIO_DATA", ROOT.parent / "project_studio_data"))
    project = argv[0] if argv else "domotica-voz"
    try:
        state_file = data / "projects" / project / "state.json"
        names = json.loads(state_file.read_text(encoding="utf-8")).get("names", {}) if state_file.exists() else {}
        token = json.loads((secrets / "ha.json").read_text(encoding="utf-8"))["token"]
        client = HaClient(os.environ.get("HA_URL", "http://127.0.0.1:8123"), token)
        entities, devices = client.ws({"type": "config/entity_registry/list"}, {"type": "config/device_registry/list"})
        # The list leaves out the aliases; read them so names already right are not written again.
        ids = [e["entity_id"] for e in entities if e.get("platform") in ("mqtt", "esphome")]
        full = client.ws({"type": "config/entity_registry/get_entries", "entity_ids": ids})[0]
        entities = [{**e, "aliases": (full.get(e["entity_id"]) or {}).get("aliases")} for e in entities]
        count = _apply(client, plan(json.loads(CATALOG.read_text(encoding="utf-8")), names, entities, devices), devices)
    except (HaError, OSError, KeyError, json.JSONDecodeError) as err:
        print(err if isinstance(err, HaError) else f"E_NAMES: {err}")
        return 1
    print(f"OK: {count} cambios de nombres y áreas en Home Assistant")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
