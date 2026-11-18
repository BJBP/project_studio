# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27", "websockets>=12"]
# ///
# End-to-end voice check without a human: Piper speaks a phrase, the audio goes through the Home Assistant
# voice pipeline (Whisper -> local AI -> Piper) and the script prints what was heard and answered.
# Usage: uv run tests/e2e/voice_pipeline.py "¿Qué hora es?"   Exit 0 = the pipeline answered.
#        uv run tests/e2e/voice_pipeline.py --wake "okay nabu, enciende el foco"   starts at the wake word (hands-free).
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
import websockets

HA_URL = os.environ.get("HA_URL", "http://127.0.0.1:8123")
HA_CONTAINER = os.environ.get("HA_CONTAINER", "domotica-voz-homeassistant-1")
SECRETS = Path.home() / ".agents" / "secrets" / "project_studio" / "ha.json"
CHUNK = 3200  # 100 ms of 16 kHz 16-bit mono audio
SILENCE = bytes(CHUNK * 20)  # 2 s: lets the detector settle and HA notice the end of the order


def speak(token: str, text: str) -> bytes:
    """Asks Piper (through Home Assistant) for the phrase and converts it to raw 16 kHz PCM with ffmpeg."""
    headers = {"Authorization": f"Bearer {token}"}
    path = httpx.post(f"{HA_URL}/api/tts_get_url", json={"engine_id": "tts.piper", "message": text},
                      headers=headers, timeout=60).json()["path"]
    audio = httpx.get(f"{HA_URL}{path}", headers=headers, timeout=60).content
    cmd = ["docker", "exec", "-i", HA_CONTAINER, "ffmpeg", "-loglevel", "error", "-i", "pipe:0",
           "-f", "s16le", "-ar", "16000", "-ac", "1", "pipe:1"]
    return subprocess.run(cmd, input=audio, capture_output=True, check=True).stdout


async def run_pipeline(token: str, pcm: bytes, wake: bool = False) -> dict:
    async with websockets.connect(HA_URL.replace("http", "ws", 1) + "/api/websocket", max_size=None) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        await ws.recv()
        start = {"start_stage": "wake_word", "input": {"sample_rate": 16000, "timeout": 30}} if wake             else {"start_stage": "stt", "input": {"sample_rate": 16000}}
        await ws.send(json.dumps({"id": 1, "type": "assist_pipeline/run", "end_stage": "tts", **start}))
        if wake:
            pcm = SILENCE + pcm + SILENCE
        found = {}
        while True:
            msg = json.loads(await ws.recv())
            event = msg.get("event", {})
            kind, data = event.get("type"), event.get("data") or {}
            if kind == "run-start":
                handler = bytes([data["runner_data"]["stt_binary_handler_id"]])
                for i in range(0, len(pcm), CHUNK):
                    await ws.send(handler + pcm[i:i + CHUNK])
                await ws.send(handler)
            elif kind == "wake_word-end":
                found["wake_word"] = (data.get("wake_word_output") or {}).get("wake_word_id")
            elif kind == "stt-end":
                found["heard"] = data["stt_output"]["text"]
            elif kind == "intent-end":
                found["answer"] = data["intent_output"]["response"]["speech"]["plain"]["speech"]
            elif kind == "tts-end":
                found["audio_url"] = data["tts_output"]["url"]
            elif kind == "error":
                found["error"] = data
                return found
            elif kind == "run-end":
                return found


def main() -> int:
    wake = "--wake" in sys.argv
    words = [a for a in sys.argv[1:] if a != "--wake"]
    phrase = words[0] if words else "¿Qué hora es?"
    token = json.loads(SECRETS.read_text(encoding="utf-8"))["token"]
    result = asyncio.run(run_pipeline(token, speak(token, phrase), wake))
    print(json.dumps(result, ensure_ascii=False))
    return 0 if "answer" in result and "audio_url" in result and (not wake or result.get("wake_word")) else 1


if __name__ == "__main__":
    sys.exit(main())
