# Checks the AI key handling of the Studio server without Home Assistant (the setup run is replaced).
# Usage: uv run --no-project --with pytest pytest tests/server -q
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import serve_ai  # noqa: E402


def test_lists_providers_without_exposing_keys(tmp_path):
    (tmp_path / "ai_keys.json").write_text(json.dumps({"claude": "secret"}), encoding="utf-8")
    providers = {p["id"]: p for p in serve_ai.public_providers(tmp_path)}
    assert providers["local"]["cloud"] is False
    assert providers["claude"]["hasKey"] is True
    assert "secret" not in json.dumps(providers)


def test_rejects_bad_input(tmp_path):
    assert serve_ai.save_key(tmp_path, "local", "abc")["code"] == "E_PROVIDER"
    assert serve_ai.save_key(tmp_path, "nope", "abc")["code"] == "E_PROVIDER"
    assert serve_ai.save_key(tmp_path, "claude", "two words")["code"] == "E_KEY_FORMAT"


def test_rejected_key_is_not_kept(tmp_path, monkeypatch):
    monkeypatch.setattr(serve_ai, "_run_setup", lambda *_: {"ok": False, "code": "E_FLOW_INVALID", "message": "x"})
    assert serve_ai.save_key(tmp_path, "claude", "bad-key")["ok"] is False
    assert json.loads((tmp_path / "ai_keys.json").read_text(encoding="utf-8")) == {}


def test_accepted_key_is_kept(tmp_path, monkeypatch):
    monkeypatch.setattr(serve_ai, "_run_setup", lambda *_: {"ok": True, "code": None, "message": "Listo."})
    assert serve_ai.save_key(tmp_path, "openai", " good-key ")["ok"] is True
    assert json.loads((tmp_path / "ai_keys.json").read_text(encoding="utf-8")) == {"openai": "good-key"}
