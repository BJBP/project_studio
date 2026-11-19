# Checks that the simulator YAML keeps the real pieces and only swaps what the emulator lacks.
# Usage: uv run --no-project --with pytest pytest tests/firmware -q
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "firmware"))
from sim_variant import sim_config  # noqa: E402


def test_the_real_device_becomes_its_simulator():
    sim = sim_config((ROOT / "firmware" / "esphome" / "circuito_maestro.yaml").read_text(encoding="utf-8"))
    assert "name: circuito-maestro-sim" in sim
    assert "friendly_name: Circuito maestro" in sim
    for kept in ("base", "oled", "relay", "buzzer"):
        assert f"  {kept}: !include packages/{kept}.yaml" in sim
    for dropped in ("wifi", "psram", "voice"):
        assert f"packages/{dropped}.yaml" not in sim
    assert "  qemu_net: !include packages/qemu_net.yaml" in sim


def test_a_yaml_without_name_is_rejected():
    with pytest.raises(ValueError):
        sim_config("packages:\n  base: !include packages/base.yaml\n")


def test_real_board_wifi_setup_listens_on_the_com_connector():
    # The cable lines (serial_bridge) use the logger's port; on the S3 the default is the native USB, not «COM».
    wifi = (ROOT / "firmware" / "esphome" / "packages" / "wifi.yaml").read_text(encoding="utf-8")
    assert "serial_bridge:" in wifi
    assert "hardware_uart: UART0" in wifi
