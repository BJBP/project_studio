# Checks the board routes of the Studio server without a board (board.py is replaced): port check, the remembered
# Wi-Fi, and that the password goes by stdin and is only saved when asked.
# Usage: uv run --no-project --with pytest pytest tests/server -q
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import serve_board  # noqa: E402


def test_bad_port_is_rejected_before_running_anything():
    assert serve_board.board_status("COM4 --erase")[0] == 400
    assert serve_board.start_flash("circuito_maestro", "../x")[0] == 400


def test_connect_uses_stdin_saves_only_when_asked_and_reports_board_errors(tmp_path, monkeypatch):
    calls = []

    def fake_board(args, stdin=None, timeout_s=120):
        calls.append((args, stdin))
        return 1, "E_WIFI_FAILED: La placa no entró en la red."
    monkeypatch.setattr(serve_board, "_board", fake_board)
    status, body = serve_board.connect(tmp_path, "COM4", "Red", "clave", remember=True, project="domotica-voz")
    assert (status, body["code"]) == (400, "E_WIFI_FAILED")
    assert "clave" not in " ".join(calls[0][0]) and json.loads(calls[0][1])["password"] == "clave"
    assert not (tmp_path / "wifi.json").exists()  # a failed connection is not remembered


def test_empty_password_uses_the_remembered_wifi(tmp_path, monkeypatch):
    (tmp_path / "wifi.json").write_text(json.dumps({"ssid": "Red", "password": "guardada"}), encoding="utf-8")
    sent = []
    monkeypatch.setattr(serve_board, "_board", lambda args, stdin=None, timeout_s=120: (sent.append(stdin), (1, "E_X: y"))[1])
    serve_board.connect(tmp_path, "COM4", "Red", "", remember=False, project="domotica-voz")
    assert json.loads(sent[0])["password"] == "guardada"
