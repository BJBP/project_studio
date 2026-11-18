# Installs the circuit modes in Home Assistant: one on/off switch per mode (input_boolean.modo_<id>) and the
# automations in ../automations/*.json. Receives an authenticated HaClient; idempotent (automations are rewritten).
import json
from pathlib import Path

from ha_client import HaClient, HaError

ROOT = Path(__file__).resolve().parents[3]
MODES_FILE = ROOT / "web" / "demos" / "voice" / "data" / "modes.example.json"
AUTOMATIONS_DIR = Path(__file__).resolve().parent.parent / "automations"


def ensure_mode_switches(client: HaClient) -> None:
    modes = [m for m in json.loads(MODES_FILE.read_text(encoding="utf-8"))["modes"] if not m.get("builtin")]
    existing = {item["id"] for item in client.ws({"type": "input_boolean/list"})[0]}
    for mode in modes:
        object_id = f"modo_{mode['id']}"
        if object_id in existing:
            continue
        client.ws({"type": "input_boolean/create", "name": f"Modo {mode['name']}", "icon": "mdi:toggle-switch"})
        # HA names the helper after its name; rename it to the stable id the automations use.
        created = next(i for i in client.ws({"type": "input_boolean/list"})[0] if i["name"] == f"Modo {mode['name']}")
        if created["id"] != object_id:
            client.ws({"type": "config/entity_registry/update", "entity_id": f"input_boolean.{created['id']}",
                       "new_entity_id": f"input_boolean.{object_id}"})
        client.ws({"type": "call_service", "domain": "input_boolean", "service": "turn_on",
                   "target": {"entity_id": f"input_boolean.{object_id}"}})


def ensure_automations(client: HaClient) -> int:
    count = 0
    for path in sorted(AUTOMATIONS_DIR.glob("*.json")):
        config = json.loads(path.read_text(encoding="utf-8"))
        result = client.post(f"/api/config/automation/config/{config['id']}", config)
        if result.get("result") != "ok":
            raise HaError("E_AUTOMATION", f"{path.name}: Home Assistant no la aceptó ({result})")
        count += 1
    return count


def ensure_modes(client: HaClient) -> int:
    ensure_mode_switches(client)
    return ensure_automations(client)
