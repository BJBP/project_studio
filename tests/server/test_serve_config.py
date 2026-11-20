# Checks the Home Assistant address the page receives: HA_PUBLIC_URL when the server reaches HA another way (Docker).
# Usage: uv run --no-project --with pytest pytest tests/server -q
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import serve  # noqa: E402


def test_page_gets_public_url_when_set(monkeypatch):
    monkeypatch.setenv("HA_URL", "http://homeassistant:8123")
    monkeypatch.setenv("HA_PUBLIC_URL", "http://127.0.0.1:8123")
    assert serve.build_config()["haUrl"] == "http://127.0.0.1:8123"


def test_page_gets_server_url_without_public_url(monkeypatch):
    monkeypatch.setenv("HA_URL", "http://127.0.0.1:9123")
    monkeypatch.delenv("HA_PUBLIC_URL", raising=False)
    assert serve.build_config()["haUrl"] == "http://127.0.0.1:9123"
