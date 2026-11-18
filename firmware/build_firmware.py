# Checks and compiles an ESPHome firmware in Docker and leaves it ready for «⚡ Instalar» in the Studio:
# web/firmware/<name>/firmware.factory.bin + manifest.json (ESP Web Tools). Secrets come from the secrets folder.
# Usage: uv run --no-project python firmware/build_firmware.py [circuito_maestro] [--check-only]
# Exit 0 = OK; otherwise "<CODE>: <what to do>" (E_DOCKER, E_NO_SECRETS, E_ESPHOME_CONFIG, E_ESPHOME_COMPILE).
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ESPHOME_IMAGE = os.environ.get("ESPHOME_IMAGE", "ghcr.io/esphome/esphome:stable")
CONFIG_DIR = Path(__file__).resolve().parent / "esphome"
WEB_FIRMWARE = Path(__file__).resolve().parents[1] / "web" / "firmware"
SECRETS = Path(os.environ.get("STUDIO_SECRETS", Path.home() / ".agents" / "secrets" / "project_studio")) / "esphome_secrets.yaml"


def esphome(command: str, config: str) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", "run", "--rm", "-v", f"{CONFIG_DIR}:/config",
                           "-v", f"{SECRETS}:/config/secrets.yaml:ro", ESPHOME_IMAGE, command, config],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def fail(code: str, message: str, output: str = "") -> int:
    if output:
        print("\n".join(output.strip().splitlines()[-25:]), file=sys.stderr)
    print(f"{code}: {message}")
    return 1


def publish(name: str, friendly: str) -> Path:
    host = name.replace("_", "-")  # the device hostname in the YAML uses dashes
    build = CONFIG_DIR / ".esphome" / "build" / host / "build" / "firmware.factory.bin"  # ESPHome 2026 + ESP-IDF layout
    target = WEB_FIRMWARE / name
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(build, target / "firmware.factory.bin")
    manifest = {"name": friendly, "version": "1.0", "new_install_prompt_erase": True,
                "builds": [{"chipFamily": "ESP32-S3", "improv": True,
                            "parts": [{"path": "firmware.factory.bin", "offset": 0}]}]}
    (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def main(argv: list) -> int:
    name = next((a for a in argv if not a.startswith("--")), "circuito_maestro")
    config = f"{name}.yaml"
    if shutil.which("docker") is None:
        return fail("E_DOCKER", "Docker no está instalado o no está en marcha. Abre Docker Desktop.")
    if not SECRETS.exists():
        return fail("E_NO_SECRETS", f"Falta {SECRETS}. Copia firmware/esphome/secrets.example.yaml allí y cambia los valores.")
    checked = esphome("config", config)
    if checked.returncode != 0:
        return fail("E_ESPHOME_CONFIG", f"{config} tiene errores (arriba).", checked.stdout + checked.stderr)
    if "--check-only" in argv:
        print(f"OK: {config} es válido.")
        return 0
    built = esphome("compile", config)
    if built.returncode != 0:
        return fail("E_ESPHOME_COMPILE", f"No compiló {config} (arriba).", built.stdout + built.stderr)
    print(f"OK: firmware listo en {publish(name, name.replace('_', ' ').capitalize())}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
