# Checks the Improv Serial packets (Wi-Fi over the cable) without a board: build, find among log lines, read results.
# Usage: uv run --no-project --with pytest pytest tests/firmware -q
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "firmware"))
import improv  # noqa: E402


def test_wifi_packet_layout_and_checksum():
    data = improv.wifi_rpc("Red", "clave1")
    assert data.startswith(b"IMPROV\x01\x03") and data.endswith(b"\n")
    body = data[:-2]
    assert data[-2] == sum(body) & 0xFF
    assert body[9:] == bytes([improv.CMD_WIFI, 11, 3]) + b"Red" + bytes([6]) + b"clave1"


def test_packets_are_found_between_log_lines_and_across_reads():
    state = improv.packet(improv.TYPE_STATE, bytes([improv.STATE_PROVISIONED]))
    stream = b"[I][wifi]: IP Address: 192.168.1.51\r\n" + state + b"[D][api]: ok\r\n"
    first, rest = improv.parse(stream[:40])
    second, _ = improv.parse(rest + stream[40:])
    assert first + second == [(improv.TYPE_STATE, bytes([improv.STATE_PROVISIONED]))]
    assert improv.ip_from_log(stream) == "192.168.1.51"


def test_bad_checksum_is_skipped():
    broken = bytearray(improv.packet(improv.TYPE_STATE, b"\x02"))
    broken[-2] ^= 0xFF
    assert improv.parse(bytes(broken))[0] == []


def test_scan_result_strings():
    payload = bytes([improv.CMD_SCAN, 11, 3]) + b"Red" + bytes([3]) + b"-50" + bytes([3]) + b"YES"
    assert improv.result_strings(payload) == (improv.CMD_SCAN, ["Red", "-50", "YES"])


class FakeLink:
    """Serial port stand-in: each write gets the next canned answer."""
    def __init__(self, answers):
        self.answers, self.pending = list(answers), b""

    def write(self, data):
        self.pending += self.answers.pop(0) if self.answers else b""

    def read(self, size):
        chunk, self.pending = self.pending[:size], self.pending[size:]
        return chunk


def _settings(url: str) -> bytes:
    return improv.packet(improv.TYPE_STATE, bytes([improv.STATE_PROVISIONED])) + improv.packet(
        improv.TYPE_RESULT, bytes([improv.CMD_STATE, len(url) + 1, len(url)]) + url.encode())


def test_state_waits_while_the_board_is_still_joining_the_network(monkeypatch):
    improv_link = pytest.importorskip("improv_link")  # needs pyserial
    monkeypatch.setattr(improv_link, "STATE_RETRY_S", 0.05)
    link = FakeLink([_settings("http://0.0.0.0"), _settings("http://192.168.1.50")])
    assert improv_link._current(link) == {"online": True, "ip": "192.168.1.50"}
