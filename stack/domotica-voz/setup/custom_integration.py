# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
# Installs a community integration (custom_components/<id>) from custom_integrations.json into the Home Assistant
# container, at its pinned GitHub tag, and restarts Home Assistant. Usage: uv run custom_integration.py sonoff
# Prints "OK: ..." or "<CODE>: what to do" (exit 1).
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import httpx

STACK = Path(__file__).resolve().parents[1]
CATALOG = STACK / "custom_integrations.json"
COMPOSE = ["docker", "compose", "-f", str(STACK / "docker-compose.yml")]


class InstallError(Exception):
    pass


def find(integration_id: str) -> dict:
    items = json.loads(CATALOG.read_text(encoding="utf-8"))["integrations"]
    found = next((i for i in items if i["id"] == integration_id), None)
    if not found:
        raise InstallError(f"E_UNKNOWN_INTEGRATION: no hay «{integration_id}» en custom_integrations.json.")
    return found


def component_files(archive: bytes, integration_id: str) -> list:
    """[(relative path, data)] of custom_components/<id>/ in the release archive (paths checked: no '..')."""
    marker = f"/custom_components/{integration_id}/"
    files = []
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        for member in tar.getmembers():
            if member.isfile() and marker in member.name and ".." not in member.name:
                files.append((member.name.split(marker, 1)[1], tar.extractfile(member).read()))
    if not files:
        raise InstallError(f"E_ARCHIVE: la versión no trae custom_components/{integration_id}.")
    return files


def container() -> str:
    found = subprocess.run([*COMPOSE, "ps", "-q", "homeassistant"], capture_output=True, text=True).stdout.strip()
    if not found:
        raise InstallError("E_HA_DOWN: Home Assistant no está en marcha. Arranca el stack de voz.")
    return found


def install(integration_id: str) -> str:
    item = find(integration_id)
    url = f"https://codeload.github.com/{item['repo']}/tar.gz/refs/tags/{item['tag']}"
    try:
        archive = httpx.get(url, timeout=60, follow_redirects=True).raise_for_status().content
    except httpx.HTTPError as err:
        raise InstallError(f"E_DOWNLOAD: no se pudo bajar {item['repo']} {item['tag']} ({err}).") from err
    target = container()
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp) / integration_id
        for name, data in component_files(archive, integration_id):
            (folder / name).parent.mkdir(parents=True, exist_ok=True)
            (folder / name).write_bytes(data)
        subprocess.run(["docker", "exec", target, "mkdir", "-p", "/config/custom_components"], check=True)
        subprocess.run(["docker", "exec", target, "rm", "-rf", f"/config/custom_components/{integration_id}"], check=True)
        subprocess.run(["docker", "cp", str(folder), f"{target}:/config/custom_components/{integration_id}"], check=True)
    subprocess.run([*COMPOSE, "restart", "homeassistant"], check=True, capture_output=True)
    return f"OK: {item['name']} {item['tag']} instalada; Home Assistant se reinicia (unos 30 s)."


def main(argv: list) -> int:
    if len(argv) != 1:
        print("E_ARGS: uso: custom_integration.py <id>")
        return 1
    try:
        print(install(argv[0]))
    except (InstallError, subprocess.CalledProcessError) as err:
        print(err if isinstance(err, InstallError) else f"E_DOCKER: {err}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
