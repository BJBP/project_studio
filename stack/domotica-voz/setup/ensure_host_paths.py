# /// script
# requires-python = ">=3.11"
# ///
# Creates, before Docker starts, every path of this computer that the two compose files mount: the data folder, the
# secrets folder, the wake words folder and esphome_secrets.yaml (random API key and OTA password). The compose files
# refuse to start without them (create_host_path: false) instead of making root-owned folders the Studio cannot write.
# Reads STUDIO_DATA_DIR, STUDIO_SECRETS_DIR, WAKE_WORDS_DIR and ESPHOME_SECRETS from the environment (as in .env).
# Exit code 0 = ready; otherwise prints "<CODE>: <what to do>" (E_SECRETS_IS_DIR, E_NOT_WRITABLE).
import base64
import os
import secrets
import sys
from pathlib import Path

STACK_DIR = Path(__file__).resolve().parents[1]  # relative paths in each .env start at its compose file
REPO_DIR = STACK_DIR.parents[1]
DEFAULT_SECRETS = "~/.agents/secrets/project_studio/esphome_secrets.yaml"
DEFAULT_WAKE_WORDS = "../../../project_studio_data/wake_words"
DEFAULT_DATA = "../project_studio_data"
DEFAULT_SECRETS_DIR = "~/.agents/secrets/project_studio"


def host_path(name: str, default: str, base: Path = STACK_DIR) -> Path:
    path = Path(os.environ.get(name, "").strip() or default).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


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


def ensure_folder(path: Path, mode: int = 0o777) -> str:
    path.mkdir(parents=True, exist_ok=True, mode=mode)
    if not os.access(path, os.W_OK):
        raise SystemExit(f"E_NOT_WRITABLE: no se puede escribir en {path} (la creó Docker como root). "
                         f"Devuélvela a tu usuario (sudo chown -R $USER {path}) y repite.")
    return f"OK: carpeta {path} lista."


def main() -> int:
    print(ensure_esphome_secrets(host_path("ESPHOME_SECRETS", DEFAULT_SECRETS)))
    print(ensure_folder(host_path("WAKE_WORDS_DIR", DEFAULT_WAKE_WORDS)))
    print(ensure_folder(host_path("STUDIO_DATA_DIR", DEFAULT_DATA, REPO_DIR)))
    print(ensure_folder(host_path("STUDIO_SECRETS_DIR", DEFAULT_SECRETS_DIR, REPO_DIR), 0o700))
    return 0


if __name__ == "__main__":
    sys.exit(main())
