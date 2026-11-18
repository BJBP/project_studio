# Local web server for the Studio: serves web/ on 127.0.0.1 and /config.json built at request time.
# The Home Assistant token is read from the secrets folder (outside the repo) and never written into web/.
# Usage: uv run --no-project python serve.py [--port 8765]
import argparse
import json
import os
import urllib.error
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from serve_ai import public_providers, save_key

WEB_DIR = Path(__file__).resolve().parent / "web"
TTS_PREFIX = "/api/tts_proxy/"  # only path relayed to HA; its links are signed, so no token is added
SECRETS_FILE = Path(os.environ.get("STUDIO_SECRETS", Path.home() / ".agents" / "secrets" / "project_studio")) / "ha.json"


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
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/ai-key":
            self.send_error(404)
            return
        # Only this page may save keys: any website (or a rebound DNS name) could otherwise post to 127.0.0.1.
        host = self.headers.get("Host", "")
        local_host = host.split(":")[0] in ("127.0.0.1", "localhost")
        if not local_host or self.headers.get("Origin") != f"http://{host}" or "json" not in self.headers.get("Content-Type", ""):
            self.send_error(403, "E_ORIGIN: solo la página del Estudio puede guardar claves.")
            return
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0))
        except (ValueError, json.JSONDecodeError):
            data = {}
        data = data if isinstance(data, dict) else {}
        result = save_key(SECRETS_FILE.parent, data.get("provider", ""), data.get("key", ""))
        self.send_json(200 if result["ok"] else 400, result)

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
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Estudio en http://127.0.0.1:{args.port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
