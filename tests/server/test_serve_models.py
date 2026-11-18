# Checks the AI model choice of the Studio server without Ollama or Home Assistant (both are replaced).
# Usage: uv run --no-project --with pytest pytest tests/server -q
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import serve_models  # noqa: E402

LOCAL = [{"id": "small:1b", "label": "small:1b", "sizeGb": 1.1}, {"id": "big:4b", "label": "big:4b", "sizeGb": 3.4}]


def fake_setup(ok):
    calls = []
    def run(secrets_dir, provider_id):
        calls.append(json.loads((secrets_dir / "ai_models.json").read_text(encoding="utf-8")))
        return {"ok": ok, "code": None if ok else "E_SETUP", "message": "x"}
    return run, calls


def test_lists_local_models_with_default_and_gpu(tmp_path, monkeypatch):
    monkeypatch.setattr(serve_models, "_ollama_models", lambda: LOCAL)
    status, data = serve_models.list_models(tmp_path, "local")
    assert status == 200
    assert [m["id"] for m in data["models"]] == ["small:1b", "big:4b"]
    assert data["current"] == serve_models.DEFAULT_LOCAL_MODEL
    assert data["gpuGb"] == 4


def test_lists_cloud_models_from_providers_file(tmp_path):
    status, data = serve_models.list_models(tmp_path, "claude")
    assert status == 200 and data["current"] is None and data["models"]


def test_saves_a_model_and_runs_setup(tmp_path, monkeypatch):
    monkeypatch.setattr(serve_models, "_ollama_models", lambda: LOCAL)
    run, calls = fake_setup(True)
    monkeypatch.setattr(serve_models, "_run_setup", run)
    status, data = serve_models.set_model(tmp_path, "local", "small:1b")
    assert status == 200 and data["current"] == "small:1b"
    assert calls == [{"local": "small:1b"}]


def test_a_model_that_fails_is_not_kept(tmp_path, monkeypatch):
    monkeypatch.setattr(serve_models, "_ollama_models", lambda: LOCAL)
    (tmp_path / "ai_models.json").write_text(json.dumps({"local": "big:4b"}), encoding="utf-8")
    run, calls = fake_setup(False)
    monkeypatch.setattr(serve_models, "_run_setup", run)
    status, data = serve_models.set_model(tmp_path, "local", "small:1b")
    assert status == 400 and data["current"] == "big:4b"
    assert calls[-1] == {"local": "big:4b"}, "the setup runs again with the previous model"


def test_rejects_unknown_model_and_provider(tmp_path, monkeypatch):
    monkeypatch.setattr(serve_models, "_ollama_models", lambda: LOCAL)
    assert serve_models.set_model(tmp_path, "local", "nope")[1]["code"] == "E_MODEL"
    assert serve_models.list_models(tmp_path, "nope")[1]["code"] == "E_PROVIDER"
