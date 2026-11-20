# Checks that the launchers' first step creates esphome_secrets.yaml with valid keys, keeps an existing one and
# reports the root-owned folder that Docker leaves when the file is missing.
# Usage: uv run --no-project --with pytest pytest tests/server -q
import base64
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "stack" / "domotica-voz" / "setup"))
import ensure_secrets  # noqa: E402


def test_creates_file_with_32_byte_key_and_private_permissions(tmp_path):
    path = tmp_path / "secrets" / "project_studio" / "esphome_secrets.yaml"
    assert ensure_secrets.ensure_esphome_secrets(path).startswith("OK: creado")
    text = path.read_text(encoding="utf-8")
    key = re.search(r'api_encryption_key: "(.+)"', text).group(1)
    assert len(base64.b64decode(key)) == 32
    assert re.search(r'ota_password: "[0-9a-f]{32}"', text)
    if sys.platform != "win32":
        assert path.stat().st_mode & 0o777 == 0o600


def test_keeps_existing_file(tmp_path):
    path = tmp_path / "esphome_secrets.yaml"
    path.write_text("api_encryption_key: \"mine\"\n", encoding="utf-8")
    assert "ya existe" in ensure_secrets.ensure_esphome_secrets(path)
    assert path.read_text(encoding="utf-8") == "api_encryption_key: \"mine\"\n"


def test_folder_left_by_docker_is_reported(tmp_path):
    path = tmp_path / "esphome_secrets.yaml"
    path.mkdir()
    with pytest.raises(SystemExit, match="E_SECRETS_IS_DIR"):
        ensure_secrets.ensure_esphome_secrets(path)


def test_path_comes_from_env_with_home_expanded(monkeypatch):
    monkeypatch.setenv("ESPHOME_SECRETS", "~/x/esphome_secrets.yaml")
    assert ensure_secrets.esphome_secrets_path() == Path.home() / "x" / "esphome_secrets.yaml"
    monkeypatch.delenv("ESPHOME_SECRETS")
    assert ensure_secrets.esphome_secrets_path() == ensure_secrets.DEFAULT_FILE
