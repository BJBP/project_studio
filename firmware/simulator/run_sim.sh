#!/bin/sh
# Boots a simulator firmware in the ESP32-S3 emulator, inside the voice stack network as "esp32-sim".
# Usage: sh firmware/simulator/run_sim.sh [circuito_maestro]   (after build_firmware.py <name> --sim)
# Home Assistant reaches the device at esp32-sim:6053, like a real board on the Wi-Fi.
set -e
NAME="${1:-circuito_maestro}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FIRMWARE="$ROOT/web/firmware/${NAME}_sim"
NETWORK="${STACK_NETWORK:-domotica-voz_default}"
IMAGE="${SIM_IMAGE:-project-studio-esp32-sim}"
FLASH_MB=16   # same flash size as the board (base.yaml)

[ -f "$FIRMWARE/firmware.factory.bin" ] || { echo "E_SIM_NO_FIRMWARE: compila antes: build_firmware.py $NAME --sim"; exit 1; }
docker image inspect "$IMAGE" >/dev/null 2>&1 || docker build -q -t "$IMAGE" "$ROOT/firmware/simulator" >/dev/null
# The emulator needs a full flash image: the factory image padded to the flash size.
cp "$FIRMWARE/firmware.factory.bin" "$FIRMWARE/flash.bin"
truncate -s "${FLASH_MB}M" "$FIRMWARE/flash.bin"
docker rm -f esp32-sim >/dev/null 2>&1 || true
docker run -d --name esp32-sim --network "$NETWORK" -v "$FIRMWARE:/fw" "$IMAGE" \
  -nographic -machine esp32s3 \
  -drive "file=/fw/flash.bin,if=mtd,format=raw" \
  -nic "user,model=open_eth,hostfwd=tcp::6053-:6053" >/dev/null
echo "OK: simulador en marcha (docker logs -f esp32-sim)"
