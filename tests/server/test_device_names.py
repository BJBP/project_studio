# Checks how the real board and its virtual twin are named in Home Assistant, and that modes act on both.
# No Home Assistant: the registry lists are made up. Usage: uv run --no-project --with pytest pytest tests/server -q
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "stack" / "domotica-voz" / "setup"))
import device_names  # noqa: E402
import modes  # noqa: E402

CATALOG = {"devices": [{"id": "lab", "name": "Lab", "area": "Taller",
                        "entities": [{"key": "relay_1", "component": "switch", "name": "Foco"}]}]}
VIRTUAL_DEVICE = {"id": "v", "name": "Lab", "manufacturer": "Project Studio", "identifiers": [["mqtt", "lab"]]}
BOARD = {"id": "b", "name": "Lab", "manufacturer": "Espressif", "identifiers": [["esphome", "aa:bb"]]}
VIRTUAL = {"entity_id": "switch.lab_relay_1", "platform": "mqtt", "unique_id": "lab_relay_1", "device_id": "v"}
REAL = {"entity_id": "switch.lab_relay_1_2", "platform": "esphome", "unique_id": "aa-switch-foco", "device_id": "b",
        "original_name": "Foco"}


def test_only_virtual_keeps_the_plain_name_and_the_project_area():
    steps = device_names.plan(CATALOG, {}, [VIRTUAL], [VIRTUAL_DEVICE])
    assert steps["entities"] == [("switch.lab_relay_1", {"name": "Foco", "aliases": ["Foco"]})]
    assert steps["areas"] == {"v": "Taller"}


def test_with_a_board_the_virtual_moves_aside_first_and_the_chosen_name_wins():
    steps = device_names.plan(CATALOG, {"lab": {"relay_1": "Ventilador"}}, [VIRTUAL, REAL], [VIRTUAL_DEVICE, BOARD])
    assert steps["entities"] == [
        ("switch.lab_relay_1", {"name": "Ventilador virtual", "aliases": ["Ventilador virtual"],
                                "new_entity_id": "switch.lab_virtual_relay_1"}),
        ("switch.lab_relay_1_2", {"name": "Ventilador", "aliases": ["Ventilador"], "new_entity_id": "switch.lab_relay_1"}),
    ]
    assert steps["areas"] == {"b": "Taller", "v": "Demo"}


def test_names_already_right_change_nothing():
    done = {**REAL, "entity_id": "switch.lab_relay_1", "name": "Foco", "aliases": ["Foco"]}
    assert device_names.plan(CATALOG, {}, [done], [BOARD])["entities"] == []


def test_mode_actions_also_reach_the_virtual_twin():
    config = {"triggers": [{"entity_id": "switch.lab_relay_1"}],
              "actions": [{"action": "switch.turn_on", "target": {"entity_id": "switch.lab_relay_1"}},
                          {"action": "notify", "target": {"entity_id": "notify.other"}}]}
    out = modes.with_virtual_twins(config, {"switch.lab_relay_1": "switch.lab_virtual_relay_1"})
    assert out["actions"][0]["target"]["entity_id"] == ["switch.lab_relay_1", "switch.lab_virtual_relay_1"]
    assert out["actions"][1]["target"]["entity_id"] == "notify.other"
    assert out["triggers"] == config["triggers"]
