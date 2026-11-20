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


def new_esphome_secrets() -> dict:
    """Every secret the firmware packages read; a new key here reaches existing files too (ensure_esphome_secrets)."""
    return {"api_encryption_key": base64.b64encode(secrets.token_bytes(32)).decode(),
            "ota_password": secrets.token_hex(16),
            "web_username": "studio",  # the board's own page (packages/web_page.yaml)
            "web_password": secrets.token_urlsafe(12),
            "time_zone": "UTC"}  # schedules in the board (packages/local_rules.yaml); change it to your zone


def as_yaml(values: dict) -> str:
    return "".join(f'{key}: "{value}"\n' for key, value in values.items())


def ensure_esphome_secrets(path: Path) -> str:
    if path.is_dir():
        raise SystemExit(f"E_SECRETS_IS_DIR: {path} es una carpeta (la creó Docker). "
                         "Bórrala (si es de root: sudo rm -r) y repite.")
    if path.exists():
        text = path.read_text(encoding="utf-8")
        present = {line.partition(":")[0].strip() for line in text.splitlines()}
        missing = {k: v for k, v in new_esphome_secrets().items() if k not in present}
        if not missing:
            return f"OK: {path} ya existe."
        path.write_text(text.rstrip("\n") + "\n" + as_yaml(missing), encoding="utf-8")
        return f"OK: {path} ya existe; añadidas {', '.join(missing)}."
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(as_yaml(new_esphome_secrets()), encoding="utf-8")
    path.chmod(0o600)
    return f"OK: creado {path} con claves nuevas."


def ensure_folder(path: Path, mode: int = 0o777) -> str:
    path.mkdir(parents=True, exist_ok=True, mode=mode)
    if not os.access(path, os.W_OK):
        raise SystemExit(f"E_NOT_WRITABLE: no se puede escribir en {path} (la creó Docker como root). "
                         f"Devuélvela a tu usuario (sudo chown -R $USER {path}) y repite.")
    return f"OK: carpeta {path} lista."


def ensure_token_file(secrets_dir: Path) -> str:
    """Empty ha_token for the speech-to-text mount; setup_ha.py fills it (empty = no name biasing)."""
    path = secrets_dir / "ha_token"
    if path.is_dir():
        raise SystemExit(f"E_SECRETS_IS_DIR: {path} es una carpeta (la creó Docker). Bórrala y repite.")
    if not path.exists():
        path.write_text("", encoding="utf-8")
        path.chmod(0o600)
    return f"OK: {path} listo."


def main() -> int:
    print(ensure_esphome_secrets(host_path("ESPHOME_SECRETS", DEFAULT_SECRETS)))
    print(ensure_folder(host_path("WAKE_WORDS_DIR", DEFAULT_WAKE_WORDS)))
    print(ensure_folder(host_path("STUDIO_DATA_DIR", DEFAULT_DATA, REPO_DIR)))
    secrets_dir = host_path("STUDIO_SECRETS_DIR", DEFAULT_SECRETS_DIR, REPO_DIR)
    print(ensure_folder(secrets_dir, 0o700))
    print(ensure_token_file(secrets_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
