# Simulador del ESP32 (mismo firmware, emulado con QEMU)

## Decisión aprobada (2026-11-18)
Ver el ESP32 tal como está configurado: compilar, instalar en un chip emulado y verlo funcionando conectado a Home
Assistant. Emulador: QEMU de Espressif (GPL-2.0, local, en Docker). Se descartó Wokwi (propietario).

## Resultado de la prueba corta
- QEMU 9.2.2 de Espressif funciona en Docker (`firmware/simulator/Dockerfile`, máquinas `esp32` y `esp32s3`).
- **ESP32-S3 + red de QEMU (OPENETH) no compila en ESPHome 2026.11**: `ethernet_component.h` usa
  `emac_rmii_clock_mode_t`, que el S3 no tiene (no tiene Ethernet interno).
- **ESP32 clásico + OPENETH sí funciona de punta a punta**: compila (5 min con el volumen de Docker), arranca en
  QEMU, toma IP, Home Assistant lo añade con su clave de cifrado (`setup/esphome_device.py`) y un interruptor
  encendido y apagado desde Home Assistant cambia en el aparato simulado.
- La compilación en un volumen de Docker (`project_studio_esphome_build`) baja de más de 1 h a unos 5 min.

## Opciones para seguir (decide el usuario)
1. **Simular con el ESP32 clásico** (recomendada): las mismas piezas y el mismo firmware; la variante del simulador
   cambia la placa y los pines. Los pines de los paquetes pasan a ser `substitutions` (también sirve para otras placas).
   Diferencia: el chip simulado no es el S3 (mismo código, distinto chip).
2. Esperar a que ESPHome admita OPENETH en el S3 (o proponerles el arreglo).

## Mockup (pestaña «Simulador» dentro de Aparatos)
```
┌ 📟 Simulador · Circuito maestro ────────── ⚙ ✕ ┐
│ ① Compilar ✅  ② Instalar ⏳  ③ Funcionando ○   │
│ ┌ Registro ───────────────────────────────────┐ │
│ │ [I][ethernet] Connected 10.0.2.15           │ │
│ │ [D][api] Home Assistant connected           │ │
│ └─────────────────────────────────────────────┘ │
│ placa: ● relé foco ON  ○ zumbador   OLED│FOCO:ON│
│ ⚠ Error al compilar: ver el registro           │
└────────────────────────────────────────────────┘
```

## Piezas ya hechas
`firmware/simulator/{Dockerfile,run_sim.sh}`, `firmware/sim_variant.py` (+ `tests/firmware/`),
`build_firmware.py --sim`, paquetes `wifi.yaml`, `psram.yaml`, `qemu_net.yaml` separados de `base.yaml`,
`stack/domotica-voz/setup/esphome_device.py`.

## Estado
Prueba hecha. `build_firmware.py --sim` aún genera la variante para el S3 (no compila): cambia con la opción 1.
