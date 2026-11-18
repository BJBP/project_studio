# Local web server for the Studio: serves web/ on 127.0.0.1 and /config.json built at request time.
# The Home Assistant token is read from the secrets folder (outside the repo) and never written into web/.
# Usage: uv run --no-project python serve.py [--port 8765]
import argparse
import json
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parent / "web"
SECRETS_FILE = Path(os.environ.get("STUDIO_SECRETS", Path.home() / ".agents" / "secrets" / "project_studio")) / "ha.json"


def build_config() -> dict:
    """Connection settings for the page; 'error' explains what to do when the stack is not ready."""
    config = {
        "haUrl": os.environ.get("HA_URL", "http://127.0.0.1:8123"),
        "mqttUrl": os.environ.get("MQTT_WS_URL", "ws://127.0.0.1:9001"),
        "haToken": None,
        "error": None,
    }
    if SECRETS_FILE.exists():
        config["haToken"] = json.loads(SECRETS_FILE.read_text(encoding="utf-8")).get("token")
    else:
        config["error"] = "E_NO_TOKEN: falta configurar Home Assistant. Abre iniciar_estudio.bat otra vez."
    return config


class StudioHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] == "/config.json":
            body = json.dumps(build_config()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

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
