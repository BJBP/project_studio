# Voice over the cable, PC side, without a board or Home Assistant (firmware/cable_voice.py).
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "firmware"))
import cable_voice  # noqa: E402


class FakeTurn:
    def __init__(self, url, token, write, on_text=None):
        self.fed, self.on_text = [], on_text

    def feed(self, pcm):
        self.fed.append(pcm)


def test_usb_mode_turns_wake_word_and_audio_into_a_turn(monkeypatch):
    monkeypatch.setattr(cable_voice, "VoiceTurn", FakeTurn)
    sent = []
    voice = cable_voice.Voice("usb", sent.append, lambda: ("http://ha", "t"))
    voice.cable_changed(True)
    assert sent == [b"@voice\t1\n"]
    assert voice.heard({"kind": "listen"}) and voice.heard({"kind": "mic", "pcm": b"ab"})
    assert voice.turn.fed == [b"ab"]
    voice.turn.on_text("lo que\tdijo")
    assert sent[-1] == b"@set\tPantalla\tlo que dijo\n"


def test_laptop_mode_leaves_the_board_alone():
    sent = []
    voice = cable_voice.Voice("laptop", sent.append, lambda: ("http://ha", "t"))
    voice.cable_changed(True)
    assert sent == [] and not voice.heard({"kind": "listen"})
