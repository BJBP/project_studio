# Local web server for the Studio: serves web/ on 127.0.0.1 and /config.json built at request time.
# The Home Assistant token is read from the secrets folder (outside the repo) and never written into web/.
# Usage: uv run --no-project python serve.py [--port 8765]
import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from serve_ai import public_providers, save_key
from serve_board import (add_to_ha, board_status, cable_status, connect, flash_status, list_ports, start_cable,
                         start_flash, stop_cable, sync_names)
from serve_firmware import build_status, start_build
from serve_models import list_models, set_model
from serve_wake import import_word, list_words, set_word
from studio.presentation.api import PREFIX as STUDIO_PREFIX, route as studio_route
from studio.presentation.wiring import build_repo, default_data_dir

WEB_DIR = Path(__file__).resolve().parent / "web"
TTS_PREFIX = "/api/tts_proxy/"  # only path relayed to HA; its links are signed, so no token is added
SECRETS_FILE = Path(os.environ.get("STUDIO_SECRETS", Path.home() / ".agents" / "secrets" / "project_studio")) / "ha.json"


MAX_SPEAK_CHARS = 600
WAKE_WORDS_DIR = default_data_dir() / "wake_words"  # own trained words; the voice stack mounts the same folder


def speak(text: str) -> tuple[int, dict]:
    """Piper (through Home Assistant) reads a text aloud; returns the relative audio path the page plays."""
    token = build_config()["haToken"]
    if not token or not text.strip():
        return 400, {"code": "E_SPEAK", "message": "Sin texto o sin Home Assistant configurado."}
    request = urllib.request.Request(os.environ.get("HA_URL", "http://127.0.0.1:8123") + "/api/tts_get_url",
                                     data=json.dumps({"engine_id": "tts.piper", "message": text}).encode("utf-8"),
                                     headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as reply:
            return 200, {"url": json.loads(reply.read())["path"]}
    except (urllib.error.URLError, OSError, KeyError, ValueError) as err:
        return 502, {"code": "E_HA_DOWN", "message": f"No se pudo generar la voz ({err})."}


def build_config() -> dict:
    """Connection settings for the page; 'error' explains what to do when the stack is not ready."""
    config = {
        "haUrl": os.environ.get("HA_URL", "http://127.0.0.1:8123"),
        "mqttUrl": os.environ.get("MQTT_WS_URL", "ws://127.0.0.1:9001"),
        "haToken": None,
        "error": None,
        "aiProviders": public_providers(SECRETS_FILE.parent),
    }
    if SECRETS_FILE.exists():
        config["haToken"] = json.loads(SECRETS_FILE.read_text(encoding="utf-8")).get("token")
    else:
        config["error"] = "E_NO_TOKEN: falta configurar Home Assistant. Abre iniciar_estudio.bat otra vez."
    return config


class StudioHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] == "/config.json":
            self.send_json(200, build_config())
            return
        if self.path.startswith(TTS_PREFIX):
            self.proxy_tts()
            return
        if self.path.startswith(STUDIO_PREFIX):
            self.send_json(*studio_route(self.server.repo, "GET", self.path))
            return
        if self.path == "/api/wake-words":
            self.send_json(*list_words(SECRETS_FILE.parent, WAKE_WORDS_DIR))
            return
        if self.path.startswith("/api/ai-models/"):
            self.send_json(*list_models(SECRETS_FILE.parent, self.path.rsplit("/", 1)[-1]))
            return
        if self.path == "/api/board/ports":
            self.send_json(*list_ports(SECRETS_FILE.parent))
            return
        if self.path.startswith("/api/board/flash/"):
            self.send_json(*flash_status(urllib.parse.unquote(self.path.removeprefix("/api/board/flash/"))))
            return
        if self.path.startswith("/api/board/cable/"):
            self.send_json(*cable_status(urllib.parse.unquote(self.path.removeprefix("/api/board/cable/"))))
            return
        if self.path.startswith("/api/firmware/status/"):
            self.send_json(*build_status(self.path.rsplit("/", 1)[-1]))
            return
        super().do_GET()

    def do_POST(self):
        # Only this page may write: any website (or a rebound DNS name) could otherwise post to 127.0.0.1.
        host = self.headers.get("Host", "")
        local_host = host.split(":")[0] in ("127.0.0.1", "localhost")
        if not local_host or self.headers.get("Origin") != f"http://{host}" or "json" not in self.headers.get("Content-Type", ""):
            self.send_error(403, "E_ORIGIN: solo la página del Estudio puede hacer cambios.")
            return
        data = self.read_json()
        if self.path == "/api/ai-key":
            result = save_key(SECRETS_FILE.parent, data.get("provider", ""), data.get("key", ""))
            self.send_json(200 if result["ok"] else 400, result)
        elif self.path == "/api/ai-model":
            self.send_json(*set_model(SECRETS_FILE.parent, str(data.get("provider", "")), str(data.get("model", ""))))
        elif self.path == "/api/wake-word":
            self.send_json(*set_word(SECRETS_FILE.parent, WAKE_WORDS_DIR, str(data.get("word", ""))))
        elif self.path == "/api/wake-word/import":
            self.send_json(*import_word(WAKE_WORDS_DIR, str(data.get("config", "")), str(data.get("model", ""))))
        elif self.path == "/api/speak":
            self.send_json(*speak(str(data.get("text", ""))[:MAX_SPEAK_CHARS]))
        elif self.path == "/api/firmware/build":
            self.send_json(*start_build(data.get("name", "")))
        elif self.path == "/api/board/flash":
            self.send_json(*start_flash(str(data.get("name", "")), str(data.get("port", ""))))
        elif self.path == "/api/board/status":
            self.send_json(*board_status(str(data.get("port", ""))))
        elif self.path == "/api/board/cable":
            port, project = str(data.get("port", "")), str(data.get("project", ""))
            self.send_json(*(start_cable(port, project) if data.get("on") else stop_cable(port)))
        elif self.path == "/api/device-names":
            self.send_json(*sync_names(str(data.get("project", ""))))
        elif self.path == "/api/board/ha":
            self.send_json(*add_to_ha(str(data.get("ip", "")), str(data.get("project", ""))))
        elif self.path == "/api/board/wifi":
            self.send_json(*connect(SECRETS_FILE.parent, str(data.get("port", "")), str(data.get("ssid", "")),
                                    str(data.get("password", "")), bool(data.get("remember")), str(data.get("project", ""))))
        elif self.path.startswith(STUDIO_PREFIX):
            self.send_json(*studio_route(self.server.repo, "POST", self.path, data))
        else:
            self.send_error(404)

    def read_json(self) -> dict:
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0))
        except (ValueError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def send_json(self, status: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def proxy_tts(self):
        """Relays HA's spoken answers so the page plays them same-origin (HA sends no CORS headers)."""
        url = os.environ.get("HA_URL", "http://127.0.0.1:8123") + self.path
        try:
            with urllib.request.urlopen(url, timeout=30) as reply:
                body, kind = reply.read(), reply.headers.get("Content-Type", "audio/mpeg")
        except (urllib.error.URLError, OSError) as err:
            self.send_error(502, f"E_HA_DOWN: no llega el audio de Home Assistant ({err})")
            return
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor local del Estudio")
    parser.add_argument("--port", type=int, default=int(os.environ.get("STUDIO_PORT", "8765")))
    args = parser.parse_args()
    handler = partial(StudioHandler, directory=str(WEB_DIR))
    server = ThreadingHTTPServer((os.environ.get("STUDIO_HOST", "127.0.0.1"), args.port), handler)
    server.repo = build_repo()  # the user's data folder: STUDIO_DATA
    print(f"Estudio en http://127.0.0.1:{args.port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
