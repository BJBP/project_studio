# Installs the circuit modes in Home Assistant: one on/off switch per mode (input_boolean.modo_<id>) and the
# automations in ../automations/<project>/*.json. Every demo catalog has its modes file (data/*modes*.json). Receives an authenticated HaClient; idempotent (automations are rewritten).
import json
from pathlib import Path

from ha_client import HaClient, HaError

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "web" / "demos" / "voice" / "data"
AUTOMATIONS_DIR = Path(__file__).resolve().parent.parent / "automations"


def ensure_mode_switches(client: HaClient) -> None:
    modes = [m for path in sorted(DATA_DIR.glob("*modes*.json"))
             for m in json.loads(path.read_text(encoding="utf-8"))["modes"] if not m.get("builtin")]
    # Check the entity ids, not the helpers' internal ids: a renamed helper keeps its first internal id.
    existing = {e["entity_id"] for e in client.ws({"type": "config/entity_registry/list"})[0]}
    for mode in modes:
        object_id = f"modo_{mode['id']}"
        if f"input_boolean.{object_id}" in existing:
            continue
        client.ws({"type": "input_boolean/create", "name": f"Modo {mode['name']}", "icon": "mdi:toggle-switch"})
        # HA names the helper after its name; rename it to the stable id the automations use.
        created = next(i for i in client.ws({"type": "input_boolean/list"})[0] if i["name"] == f"Modo {mode['name']}")
        if created["id"] != object_id:
            client.ws({"type": "config/entity_registry/update", "entity_id": f"input_boolean.{created['id']}",
                       "new_entity_id": f"input_boolean.{object_id}"})
        client.ws({"type": "call_service", "domain": "input_boolean", "service": "turn_on",
                   "target": {"entity_id": f"input_boolean.{object_id}"}})


def virtual_twins() -> dict:
    """{entity id: its virtual twin's id} for every demo catalog entity (device_names.py names the twin)."""
    return {f"{e['component']}.{d['id']}_{e['key']}": f"{e['component']}.{d['id']}_virtual_{e['key']}"
            for path in sorted(DATA_DIR.glob("devices*.json"))
            for d in json.loads(path.read_text(encoding="utf-8")).get("devices", []) for e in d.get("entities", [])}


def with_virtual_twins(config: dict, twins: dict) -> dict:
    """Actions on a catalog entity also act on its virtual twin, so a mode moves the real board and the demo at once.
    A twin that does not exist (no real board yet) is skipped by Home Assistant."""
    def expand(node):
        if isinstance(node, list):
            return [expand(n) for n in node]
        if not isinstance(node, dict):
            return node
        out = {k: expand(v) for k, v in node.items()}
        ids = [out["entity_id"]] if isinstance(out.get("entity_id"), str) else out.get("entity_id")
        if isinstance(ids, list) and any(i in twins for i in ids):
            out["entity_id"] = ids + [twins[i] for i in ids if i in twins]
        return out
    return {**config, "actions": expand(config.get("actions", []))}


def ensure_automations(client: HaClient) -> int:
    count, twins = 0, virtual_twins()
    for path in sorted(AUTOMATIONS_DIR.glob("**/*.json")):
        config = with_virtual_twins(json.loads(path.read_text(encoding="utf-8")), twins)
        result = client.post(f"/api/config/automation/config/{config['id']}", config)
        if result.get("result") != "ok":
            raise HaError("E_AUTOMATION", f"{path.name}: Home Assistant no la aceptó ({result})")
        count += 1
    return count


def ensure_modes(client: HaClient) -> int:
    ensure_mode_switches(client)
    return ensure_automations(client)
