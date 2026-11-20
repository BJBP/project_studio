# Checks the cable lines and the Home Assistant stand-in of cable mode without a board or MQTT (firmware/cable.py).
# Usage: uv run --no-project --with pytest pytest tests/firmware -q
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "firmware"))
import cable  # noqa: E402

DEVICE = {"id": "lab", "name": "Lab", "entities": [
    {"key": "foco", "component": "switch", "name": "Foco"},
    {"key": "alarma", "component": "button", "name": "Alarma"},
    {"key": "oled", "component": "text", "name": "Pantalla", "max": 64},
    {"key": "mic", "component": "sensor", "name": "Nivel"}]}


def test_board_lines_are_read_and_log_lines_skipped():
    assert cable.parse(b"\x1b[0;32m@state\tswitch\tFoco\ton\r\n") == {"kind": "state", "domain": "switch", "name": "Foco", "value": "on"}
    assert cable.parse(b"@wifi\t1\t192.168.1.9\r\n") == {"kind": "wifi", "online": True, "ip": "192.168.1.9"}
    assert cable.parse(b"@wifi\t0\t\r\n") == {"kind": "wifi", "online": False, "ip": None}
    assert cable.parse(b"[I][wifi:123]: Connected\r\n") is None
    assert cable.parse(b"") is None


def test_lines_to_the_board_refuse_tabs_and_newlines():
    assert cable.set_line("Foco", "on") == b"@set\tFoco\ton\n"
    with pytest.raises(ValueError):
        cable.wifi_line("Red", "clave\tcon tab")


def test_stand_in_uses_the_chosen_names_and_its_own_ids():
    found = dict(cable.discovery("studio", DEVICE, {"foco": "Ventilador"}))
    foco = json.loads(found["homeassistant/switch/lab_cable/foco/config"])
    assert (foco["name"], foco["default_entity_id"]) == ("Ventilador", "switch.lab_cable_foco")
    assert "state_topic" not in json.loads(found["homeassistant/button/lab_cable/alarma/config"])
    assert not any("/mic/" in topic for topic in found)  # the mic level needs Wi-Fi
    assert all(payload == "" for _, payload in cable.removal(DEVICE))


def test_states_and_orders_cross_the_cable():
    state = {"kind": "state", "domain": "switch", "name": "Foco", "value": "on"}
    assert cable.state_message("studio", DEVICE, state) == ("studio/lab_cable/foco/state", "ON")
    assert cable.state_message("studio", DEVICE, {**state, "name": "Otro"}) is None
    assert cable.command_line("studio", DEVICE, "studio/lab_cable/foco/set", "OFF") == b"@set\tFoco\toff\n"
    assert cable.command_line("studio", DEVICE, "studio/other/foco/set", "OFF") is None


def test_voice_finds_the_stand_in_by_the_chosen_name():
    assert cable.entity_ids(DEVICE, via_cable=False)[0] == "switch.lab_foco"
    assert cable.voice_aliases(DEVICE, {"foco": "Ventilador"})[:2] == [
        ("switch.lab_cable_foco", "Ventilador"), ("button.lab_cable_alarma", "Alarma")]


def test_voice_lines_round_trip_audio_and_stay_under_the_board_limit():
    pcm = bytes(range(256)) * 20
    lines = cable.speaker_lines(pcm)
    assert all(len(line) < 4096 for line in lines)
    back = b"".join(cable.parse(line.replace(b"@spk", b"@mic"))["pcm"] for line in lines)
    assert back == pcm
    assert cable.parse(b"@listen\r\n") == {"kind": "listen"}
    assert cable.parse(b"@mic\tno*base64\r\n") is None
    assert cable.voice_line(True) == b"@voice\t1\n" and cable.play_line(16000) == b"@play\t16000\n"


def test_cable_takes_over_when_wifi_is_down_or_stuck():
    assert cable.cable_needed(board_online=False, ha_misses=0)
    assert not cable.cable_needed(board_online=True, ha_misses=cable.HA_MISSES_FOR_CABLE - 1)
    assert cable.cable_needed(board_online=True, ha_misses=cable.HA_MISSES_FOR_CABLE)
