# Checks that the voice agent's sub-entry flow is started again when Home Assistant drops it just after a restart
# (404 «Invalid flow specified»), and that other errors still stop the setup.
# Usage: uv run --no-project --with pytest --with httpx --with websockets pytest tests/server -q
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "stack" / "domotica-voz" / "setup"))
import agents  # noqa: E402
from ha_client import HaError  # noqa: E402

DROPPED = HaError("E_HA_HTTP", '/api/config/config_entries/subentries/flow/abc -> 404: {"message":"Invalid flow specified"}')


class FakeClient:
    def __init__(self, failures: list):
        self.failures = failures  # errors raised by the second step, in order
        self.started = 0

    def post(self, path: str, payload: dict) -> dict:
        if path.endswith("/subentries/flow"):
            self.started += 1
            return {"flow_id": f"f{self.started}"}
        if self.failures:
            raise self.failures.pop(0)
        return {"type": "create_entry"}


def test_dropped_flow_is_started_again():
    client = FakeClient([DROPPED])
    assert agents.run_subentry_flow(client, {}, {}, wait_s=0) == {"type": "create_entry"}
    assert client.started == 2


def test_gives_up_after_the_last_attempt():
    client = FakeClient([DROPPED, DROPPED, DROPPED])
    with pytest.raises(HaError, match="Invalid flow"):
        agents.run_subentry_flow(client, {}, {}, attempts=3, wait_s=0)
    assert client.started == 3


def test_other_errors_are_not_retried():
    client = FakeClient([HaError("E_HA_HTTP", "... -> 400: bad options")])
    with pytest.raises(HaError, match="400"):
        agents.run_subentry_flow(client, {}, {}, wait_s=0)
    assert client.started == 1
