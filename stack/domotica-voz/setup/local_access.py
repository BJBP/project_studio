# Where this computer's voice stack answers, for the Studio's helper processes (cable bridge, connections):
# stack_port(name, default) -> a port from the environment or the stack's .env; ha_access() -> (Home Assistant URL, token).
import json
import os
from pathlib import Path

STACK_ENV = Path(__file__).resolve().parents[1] / ".env"
SECRETS = Path(os.environ.get("STUDIO_SECRETS", Path.home() / ".agents" / "secrets" / "project_studio"))


def stack_port(name: str, default: str) -> str:
    """A port from the environment (the launcher sets it), else from the voice stack's .env, else the default."""
    if name in os.environ:
        return os.environ[name]
    lines = STACK_ENV.read_text(encoding="utf-8").splitlines() if STACK_ENV.exists() else []
    return next((line.split("=", 1)[1].strip() for line in lines if line.startswith(f"{name}=")), default)


def ha_access() -> tuple[str, str]:
    """(Home Assistant URL, token)."""
    token = json.loads((SECRETS / "ha.json").read_text(encoding="utf-8"))["token"]
    return os.environ.get("HA_URL", f"http://127.0.0.1:{stack_port('HA_PORT', '8123')}"), token
