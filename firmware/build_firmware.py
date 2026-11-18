# Checks and compiles an ESPHome firmware in Docker and leaves it ready for «⚡ Instalar» in the Studio:
# web/firmware/<name>/firmware.factory.bin + manifest.json (ESP Web Tools). Secrets come from the secrets folder.
# Usage: uv run --no-project python firmware/build_firmware.py [circuito_maestro] [--check-only] [--sim]
# --sim builds the simulator version (sim_variant.py) into web/firmware/<name>_sim/ for the ESP32 emulator.
# Exit 0 = OK; otherwise "<CODE>: <what to do>" (E_DOCKER, E_NO_SECRETS, E_ESPHOME_CONFIG, E_ESPHOME_COMPILE).
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from sim_variant import sim_config

ESPHOME_IMAGE = os.environ.get("ESPHOME_IMAGE", "ghcr.io/esphome/esphome:stable")
CONFIG_DIR = Path(__file__).resolve().parent / "esphome"
WEB_FIRMWARE = Path(__file__).resolve().parents[1] / "web" / "firmware"
# Build files live in a Docker volume: on a Windows folder the first ESP-IDF build took over an hour.
BUILD_VOLUME = os.environ.get("ESPHOME_BUILD_VOLUME", "project_studio_esphome_build")
SECRETS = Path(os.environ.get("STUDIO_SECRETS", Path.home() / ".agents" / "secrets" / "project_studio")) / "esphome_secrets.yaml"


def esphome(command: str, config: str) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", "run", "--rm", "-v", f"{CONFIG_DIR}:/config", "-v", f"{BUILD_VOLUME}:/config/.esphome",
                           "-v", f"{SECRETS}:/config/secrets.yaml:ro", ESPHOME_IMAGE, command, config],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def fail(code: str, message: str, output: str = "") -> int:
    if output:
        print("\n".join(output.strip().splitlines()[-25:]), file=sys.stderr)
    print(f"{code}: {message}")
    return 1


def publish(name: str, friendly: str, sim: bool = False) -> Path:
    host = name.replace("_", "-")  # the device hostname in the YAML uses dashes
    target = WEB_FIRMWARE / name
    target.mkdir(parents=True, exist_ok=True)
    built = f"/config/.esphome/build/{host}/build/firmware.factory.bin"  # ESPHome 2026 + ESP-IDF layout
    subprocess.run(["docker", "run", "--rm", "--entrypoint", "cp", "-v", f"{BUILD_VOLUME}:/config/.esphome:ro",
                    "-v", f"{target}:/out", ESPHOME_IMAGE, built, "/out/firmware.factory.bin"], check=True)
    if sim:  # the emulator boots the image directly; ESP Web Tools needs no manifest for it
        return target
    manifest = {"name": friendly, "version": "1.0", "new_install_prompt_erase": True,
                "builds": [{"chipFamily": "ESP32-S3", "improv": True,
                            "parts": [{"path": "firmware.factory.bin", "offset": 0}]}]}
    (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def main(argv: list) -> int:
    name = next((a for a in argv if not a.startswith("--")), "circuito_maestro")
    sim = "--sim" in argv
    if sim:  # generated from the real YAML each time, so the simulator never drifts from the board
        real = (CONFIG_DIR / f"{name}.yaml").read_text(encoding="utf-8")
        name = f"{name}_sim"
        (CONFIG_DIR / f"{name}.yaml").write_text(sim_config(real), encoding="utf-8")
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
    print(f"OK: firmware listo en {publish(name, name.replace('_', ' ').capitalize(), sim)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
