# Cable mode on its own (serve_cable_auto.py): when it starts the bridge, and that unticking the box is remembered.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import serve_cable_auto as auto  # noqa: E402

PORTS = [{"port": "COM3", "connector": "usb"}, {"port": "COM4", "connector": "com"}]


def test_starts_on_the_com_connector_unless_busy_or_turned_off():
    assert auto.port_to_start({"auto": True}, PORTS, {}) == "COM4"
    assert auto.port_to_start({"auto": True}, PORTS, {"cable:COM4": "running"}) is None
    assert auto.port_to_start({"auto": True}, PORTS, {"flash:COM4": "running"}) is None
    assert auto.port_to_start({"auto": True}, PORTS, {"busy:COM4": "running"}) is None
    assert auto.port_to_start({"auto": False}, PORTS, {}) is None
    assert auto.port_to_start({"auto": True}, [], {}) is None


def test_the_choice_is_kept_in_the_data_folder(tmp_path):
    assert auto.load(tmp_path)["auto"] is True
    auto.remember(tmp_path, False, "casa", "usb")
    assert auto.load(tmp_path) == {"auto": False, "project": "casa", "voice": "usb"}
