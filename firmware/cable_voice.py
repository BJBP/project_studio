# Voice over the USB cable, PC side: after "Okay Nabu" the board streams its microphone (@mic); this runs the Home
# Assistant voice pipeline with that audio (speech to text, then the assistant), asks Piper for the answer as 16 kHz
# WAV and plays it on the board's speaker (@spk). One VoiceTurn per wake word, in its own thread.
# Receives: the HA URL and token, and write(bytes) to send lines to the board. Errors end the turn with "@end".
import asyncio
import io
import json
import queue
import threading
import time
import wave

import httpx
import websockets

import cable

SAMPLE_RATE = 16000
TURN_TIMEOUT_S = 30
PRE_BUFFER_S = 0.3  # the speaker gets a little ahead, then the audio goes at playback speed
VOICE_MODES = ("laptop", "usb", "ethernet")
SCREEN = "Pantalla"  # the board's text entity: shows what was heard and the answer


class VoiceTurn:
    def __init__(self, ha_url: str, token: str, write, on_text=None):
        self.ha_url, self.token, self.write, self.on_text = ha_url.rstrip("/"), token, write, on_text
        self.audio = queue.Queue()
        threading.Thread(target=lambda: asyncio.run(self._run()), daemon=True).start()

    def feed(self, pcm: bytes) -> None:
        self.audio.put(pcm)

    async def _run(self) -> None:
        try:
            answer = await asyncio.wait_for(self._pipeline(), TURN_TIMEOUT_S)
            if answer:
                self._say(answer)
        except Exception as err:  # the board must always get "@end", whatever failed (network, HA, audio)
            print(f"AVISO E_CABLE_VOICE: {err}", flush=True)
        finally:
            self.write(cable.END_LINE)

    async def _pipeline(self) -> str:
        """Streams the microphone to Home Assistant until it hears the end of the sentence; returns the answer text."""
        url = self.ha_url.replace("http", "ws", 1) + "/api/websocket"
        async with websockets.connect(url, max_size=None) as sock:
            await sock.recv()
            await sock.send(json.dumps({"type": "auth", "access_token": self.token}))
            await sock.recv()
            await sock.send(json.dumps({"id": 1, "type": "assist_pipeline/run", "start_stage": "stt",
                                        "end_stage": "intent", "input": {"sample_rate": SAMPLE_RATE}}))
            handler, sender = None, None
            async for raw in sock:
                event = json.loads(raw)
                kind, data = event.get("event", {}).get("type"), event.get("event", {}).get("data") or {}
                if kind == "run-start":
                    handler = data["runner_data"]["stt_binary_handler_id"]
                    sender = asyncio.create_task(self._send_audio(sock, handler))
                elif kind in ("stt-vad-end", "stt-end"):
                    self.write(cable.STOP_LINE)
                    self.audio.put(b"")  # the sentence ended: stop sending audio
                    if kind == "stt-end" and self.on_text:
                        self.on_text(data.get("stt_output", {}).get("text", ""))
                elif kind == "intent-end":
                    return data["intent_output"]["response"]["speech"]["plain"]["speech"]
                elif kind in ("error", "run-end") or event.get("success") is False:
                    if sender:
                        sender.cancel()
                    return ""
        return ""

    async def _send_audio(self, sock, handler: int) -> None:
        prefix = bytes([handler])
        while True:
            try:
                chunk = await asyncio.to_thread(self.audio.get, True, TURN_TIMEOUT_S)
            except queue.Empty:
                break
            if not chunk:
                break
            await sock.send(prefix + chunk)
        await sock.send(prefix)  # no more audio

    def _say(self, text: str) -> None:
        if self.on_text:
            self.on_text(text)
        headers = {"Authorization": f"Bearer {self.token}"}
        reply = httpx.post(f"{self.ha_url}/api/tts_get_url", headers=headers, timeout=60, json={
            "engine_id": "tts.piper", "message": text,
            "options": {"preferred_format": "wav", "preferred_sample_rate": SAMPLE_RATE, "preferred_sample_channels": 1}})
        audio = httpx.get(self.ha_url + reply.raise_for_status().json()["path"], timeout=60).raise_for_status().content
        with wave.open(io.BytesIO(audio)) as wav:
            rate, pcm = wav.getframerate(), wav.readframes(wav.getnframes())
        self.write(cable.play_line(rate))
        start, sent = time.monotonic(), 0
        for line in cable.speaker_lines(pcm):
            self.write(line)
            sent += cable.SPK_CHUNK
            ahead = sent / (rate * 2) - (time.monotonic() - start)
            if ahead > PRE_BUFFER_S:
                time.sleep(ahead - PRE_BUFFER_S)
        time.sleep(max(0.0, sent / (rate * 2) - (time.monotonic() - start)))  # let it finish before "@end"


def screen_line(text: str) -> bytes:
    """What was heard or answered, on the board's screen (one line, no tabs)."""
    return cable.set_line(SCREEN, " ".join(text.split())[:64])


class Voice:
    """Voice over the cable (--voice usb): turns "@listen" into a VoiceTurn and passes it the "@mic" audio."""

    def __init__(self, mode: str, send, ha_access):
        self.mode, self.send, self.ha_access, self.turn = mode, send, ha_access, None

    def cable_changed(self, on_cable: bool) -> None:
        if self.mode == "usb":
            self.send(cable.voice_line(on_cable))  # the board listens for "Okay Nabu" only while on the cable

    def heard(self, found: dict) -> bool:
        if self.mode != "usb" or found["kind"] not in ("listen", "mic"):
            return False
        if found["kind"] == "listen":
            url, token = self.ha_access()
            self.turn = VoiceTurn(url, token, self.send, on_text=lambda text: self.send(screen_line(text)))
        elif self.turn:
            self.turn.feed(found["pcm"])
        return True
