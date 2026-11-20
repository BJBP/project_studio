# /// script
# requires-python = ">=3.11"
# ///
# Creates the secrets folder and esphome_secrets.yaml (random API key and OTA password) before Docker starts, so
# Docker never makes a root-owned folder in their place. Reads ESPHOME_SECRETS (path of the file) from the environment.
# Exit code 0 = ready; otherwise prints "<CODE>: <what to do>" (E_SECRETS_IS_DIR).
import base64
import os
import secrets
import sys
from pathlib import Path

DEFAULT_FILE = Path.home() / ".agents" / "secrets" / "project_studio" / "esphome_secrets.yaml"


def esphome_secrets_path() -> Path:
    value = os.environ.get("ESPHOME_SECRETS", "").strip()
    return Path(value).expanduser() if value else DEFAULT_FILE


def new_esphome_secrets() -> str:
    key = base64.b64encode(secrets.token_bytes(32)).decode()
    return f'api_encryption_key: "{key}"\nota_password: "{secrets.token_hex(16)}"\n'


def ensure_esphome_secrets(path: Path) -> str:
    if path.is_dir():
        raise SystemExit(f"E_SECRETS_IS_DIR: {path} es una carpeta (la creó Docker). "
                         "Bórrala (si es de root: sudo rm -r) y repite.")
    if path.exists():
        return f"OK: {path} ya existe."
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(new_esphome_secrets(), encoding="utf-8")
    path.chmod(0o600)
    return f"OK: creado {path} con claves nuevas."


def main() -> int:
    print(ensure_esphome_secrets(esphome_secrets_path()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
