# Checks the wake word choice and import of the Studio server without Docker or Home Assistant (both are replaced).
# Usage: uv run --no-project --with pytest pytest tests/server -q
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import serve_wake  # noqa: E402

MODEL = base64.b64encode(b"\x1c\x00\x00\x00TFL3" + bytes(64)).decode()
CONFIG = json.dumps({"type": "micro", "wake_word": "Oye Casa", "model": "whatever.tflite", "micro": {}})


def test_imports_a_trained_word_and_lists_it(tmp_path, monkeypatch):
    monkeypatch.setattr(serve_wake, "_restart_detector", lambda: True)
    status, result = serve_wake.import_word(tmp_path, CONFIG, MODEL)
    assert status == 200 and result["id"] == "oye_casa"
    saved = json.loads((tmp_path / "oye_casa.json").read_text(encoding="utf-8"))
    assert saved["model"] == "oye_casa.tflite" and (tmp_path / "oye_casa.tflite").exists()
    words = serve_wake.list_words(tmp_path, tmp_path)[1]["words"]
    assert {"id": "oye_casa", "name": "Oye Casa", "own": True} in words
    assert words[0]["id"] == "okay_nabu"


def test_rejects_files_that_are_not_a_wake_word(tmp_path):
    assert serve_wake.import_word(tmp_path, "{not json", MODEL)[1]["code"] == "E_WAKE_FILES"
    assert serve_wake.import_word(tmp_path, json.dumps({"type": "other", "wake_word": "x"}), MODEL)[1]["code"] == "E_WAKE_FILES"
    bad_model = base64.b64encode(b"not a model at all").decode()
    assert serve_wake.import_word(tmp_path, CONFIG, bad_model)[1]["code"] == "E_WAKE_FILES"
    builtin = json.dumps({"type": "micro", "wake_word": "Hey Jarvis"})
    assert serve_wake.import_word(tmp_path, builtin, MODEL)[1]["code"] == "E_WAKE_EXISTS"
    assert not list(tmp_path.glob("*.tflite"))


def test_a_name_cannot_escape_the_words_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(serve_wake, "_restart_detector", lambda: True)
    config = json.dumps({"type": "micro", "wake_word": "../../evil"})
    status, result = serve_wake.import_word(tmp_path, config, MODEL)
    assert status == 200 and result["id"] == "evil" and (tmp_path / "evil.json").exists()


def test_choosing_a_word_runs_setup_and_keeps_the_old_one_on_failure(tmp_path, monkeypatch):
    results = iter([{"ok": True, "code": None, "message": "Listo."}, {"ok": False, "code": "E_SETUP", "message": "x"}])
    monkeypatch.setattr(serve_wake, "_run_setup", lambda secrets, provider: next(results))
    assert serve_wake.set_word(tmp_path, tmp_path, "hey_jarvis")[1]["current"] == "hey_jarvis"
    status, result = serve_wake.set_word(tmp_path, tmp_path, "alexa")
    assert status == 400 and result["current"] == "hey_jarvis"
    assert serve_wake.list_words(tmp_path, tmp_path)[1]["current"] == "hey_jarvis"
    assert serve_wake.set_word(tmp_path, tmp_path, "nope")[1]["code"] == "E_WAKE_WORD"
