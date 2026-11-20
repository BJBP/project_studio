# Checks that the launchers' first step creates the paths Docker mounts: esphome_secrets.yaml with valid keys (an
# existing one is kept) and the wake words folder, and reports the root-owned folders Docker leaves when one is missing.
# Usage: uv run --no-project --with pytest pytest tests/server -q
import base64
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "stack" / "domotica-voz" / "setup"))
import ensure_host_paths as hp  # noqa: E402


def test_creates_secrets_with_32_byte_key_and_private_permissions(tmp_path):
    path = tmp_path / "secrets" / "project_studio" / "esphome_secrets.yaml"
    assert hp.ensure_esphome_secrets(path).startswith("OK: creado")
    text = path.read_text(encoding="utf-8")
    key = re.search(r'api_encryption_key: "(.+)"', text).group(1)
    assert len(base64.b64decode(key)) == 32
    assert re.search(r'ota_password: "[0-9a-f]{32}"', text)
    if sys.platform != "win32":
        assert path.stat().st_mode & 0o777 == 0o600


def test_keeps_existing_secrets_and_adds_only_the_missing_ones(tmp_path):
    path = tmp_path / "esphome_secrets.yaml"
    path.write_text("api_encryption_key: \"mine\"\n", encoding="utf-8")
    assert "añadidas ota_password" in hp.ensure_esphome_secrets(path)
    text = path.read_text(encoding="utf-8")
    assert text.startswith("api_encryption_key: \"mine\"\n") and text.count("api_encryption_key") == 1
    assert re.search(r'web_password: ".{12,}"', text) and 'time_zone: "UTC"' in text
    assert "ya existe." in hp.ensure_esphome_secrets(path)


def test_secrets_folder_left_by_docker_is_reported(tmp_path):
    path = tmp_path / "esphome_secrets.yaml"
    path.mkdir()
    with pytest.raises(SystemExit, match="E_SECRETS_IS_DIR"):
        hp.ensure_esphome_secrets(path)


def test_creates_wake_words_folder(tmp_path):
    path = tmp_path / "project_studio_data" / "wake_words"
    assert hp.ensure_folder(path).startswith("OK")
    assert path.is_dir()


@pytest.mark.skipif(sys.platform == "win32" or os.geteuid() == 0, reason="needs a non-root POSIX user")
def test_read_only_folder_is_reported(tmp_path):
    path = tmp_path / "wake_words"
    path.mkdir()
    path.chmod(0o500)
    try:
        with pytest.raises(SystemExit, match="E_NOT_WRITABLE"):
            hp.ensure_folder(path)
    finally:
        path.chmod(0o700)


def test_paths_come_from_env_relative_to_the_stack(monkeypatch, tmp_path):
    monkeypatch.setenv("ESPHOME_SECRETS", "~/x/esphome_secrets.yaml")
    assert hp.host_path("ESPHOME_SECRETS", hp.DEFAULT_SECRETS) == Path.home() / "x" / "esphome_secrets.yaml"
    monkeypatch.delenv("WAKE_WORDS_DIR", raising=False)
    stack = tmp_path / "repo" / "stack" / "domotica-voz"
    assert hp.host_path("WAKE_WORDS_DIR", hp.DEFAULT_WAKE_WORDS, stack) == (tmp_path / "project_studio_data" / "wake_words").resolve()


def test_root_compose_folders_default_next_to_the_repo(monkeypatch):
    monkeypatch.delenv("STUDIO_DATA_DIR", raising=False)
    data = hp.host_path("STUDIO_DATA_DIR", hp.DEFAULT_DATA, hp.REPO_DIR)
    assert data == hp.REPO_DIR.parent / "project_studio_data"
    assert hp.host_path("WAKE_WORDS_DIR", hp.DEFAULT_WAKE_WORDS) == data / "wake_words"


def test_token_file_is_created_empty_and_never_overwritten(tmp_path):
    token = tmp_path / "ha_token"
    hp.ensure_token_file(tmp_path)
    assert token.read_text(encoding="utf-8") == ""  # empty = speech-to-text starts without name biasing
    token.write_text("abc", encoding="utf-8")
    hp.ensure_token_file(tmp_path)
    assert token.read_text(encoding="utf-8") == "abc"
