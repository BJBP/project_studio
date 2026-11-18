# ESP32-S3 emulator (Espressif's QEMU, GPL-2.0) that runs the same ESPHome firmware as the real board.
# Build: docker build -t project-studio-esp32-sim firmware/simulator
# Base with CA certificates already inside, so Debian packages come over HTTPS (some networks block plain HTTP).
FROM python:3.12-slim-trixie
ARG QEMU_RELEASE=esp-develop-9.2.2-20261109
ARG QEMU_FILE=qemu-xtensa-softmmu-esp_develop_9.2.2_20261109-x86_64-linux-gnu.tar.xz
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
 && apt-get update \
 && apt-get install -y --no-install-recommends curl xz-utils libglib2.0-0t64 libpixman-1-0 libslirp0 libsdl2-2.0-0 libgcrypt20 \
 && curl -fsSL "https://github.com/espressif/qemu/releases/download/${QEMU_RELEASE}/${QEMU_FILE}" | tar -xJ -C /opt \
 && apt-get purge -y curl xz-utils && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
ENV PATH=/opt/qemu/bin:$PATH
ENTRYPOINT ["qemu-system-xtensa"]
