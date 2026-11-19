# Checks setup_ha.py and its flows against newer Home Assistant answers (404 after onboarding, abort reasons).
# Usage: uv run --no-project --with pytest --with httpx --with websockets pytest tests/server -q
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "stack" / "domotica-voz" / "setup"))
import setup_ha  # noqa: E402


def test_onboarded_ha_counts_as_up(monkeypatch):
    def fake_get(url, timeout):
        return SimpleNamespace(status_code=404 if url.endswith("/api/onboarding") else 200)
    monkeypatch.setattr(setup_ha.httpx, "get", fake_get)
    setup_ha.wait_for_ha(timeout_s=1)  # would raise E_HA_DOWN with the old /api/onboarding check


def test_a_device_already_in_ha_is_not_an_error():
    import flows

    class Client:
        def post(self, path, body):
            return {"type": "abort", "reason": "already_configured_updates"}
    assert flows.run_flow(Client(), "esphome", {})["reason"] == "already_configured_updates"
