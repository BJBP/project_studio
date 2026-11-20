# matterbridge.py: Alexa and Google get only what the voice assistant sees, over the Home Assistant WebSocket.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "stack" / "domotica-voz" / "setup"))
import matterbridge  # noqa: E402


def test_only_entities_exposed_to_the_voice_assistant_reach_matter():
    exposed = {"switch.lamp": {"conversation": True}, "sensor.mic": {"conversation": False}, "light.hall": {}}
    config = matterbridge.bridge_config("http://127.0.0.1:8124", "t", exposed)
    assert config["entityWhiteList"] == ["switch.lamp"]
    assert config["host"] == "ws://127.0.0.1:8124" and config["token"] == "t"


def test_versions_are_pinned():
    assert all(v[0].isdigit() and v.count(".") == 2 for v in matterbridge.VERSIONS.values())
