# Builds the simulator version of a device from its real ESPHome YAML, so both always have the same pieces.
# sim_config(text) -> text: drops the packages the emulator lacks (Wi-Fi, PSRAM, I2S voice), adds QEMU's network and
# renames the node "<name>-sim" (own build folder; the friendly name, and so the HA entity ids, stay the same).
import re

REAL_ONLY_PACKAGES = ("wifi", "psram", "voice")
SIM_PACKAGES = {"qemu_net": "packages/qemu_net.yaml"}
SIM_SUFFIX = "-sim"
PACKAGE_LINE = re.compile(r"^  (\w+): !include \S+\s*$")
NAME_LINE = re.compile(r"^(  name: )([\w-]+)(.*)$")


def sim_config(text: str) -> str:
    out, in_packages, renamed = [], False, False
    for line in text.splitlines():
        if line.startswith("packages:"):
            in_packages = True
            out.append(line)
            out.extend(f"  {key}: !include {path}" for key, path in SIM_PACKAGES.items())
            continue
        if in_packages and line and not line.startswith(" "):
            in_packages = False
        package = PACKAGE_LINE.match(line) if in_packages else None
        if package and package.group(1) in REAL_ONLY_PACKAGES:
            continue
        name = NAME_LINE.match(line) if not renamed and not in_packages else None
        if name:
            line, renamed = f"{name.group(1)}{name.group(2)}{SIM_SUFFIX}{name.group(3)}", True
        out.append(line)
    if not renamed:
        raise ValueError("El YAML no tiene «substitutions: name: ...»: no se puede crear la versión del simulador.")
    return "\n".join(out) + "\n"
