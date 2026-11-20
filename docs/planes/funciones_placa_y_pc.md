# Funciones en la placa y en el PC

Estado: **plan aprobado (2026-11-20)**. Fase 0 hecha: la presentación lo cuenta. Las fases 1 a 4 aún no se
construyen.

## Idea
Cada función (relé, temporizador, horario, página del celular, palabra para despertar, entender la frase…) dice en qué
lugares puede correr: **placa** (ESP32 con ESPHome), **PC** (o mini PC) o **nube**. La persona usuaria elige el lugar en
el Estudio. Elegir «placa» incluye un paquete de ESPHome al compilar. Elegir «PC» activa un servicio o una integración
de Home Assistant. Si el PC se apaga, la placa sigue con lo suyo.

## Decisiones aprobadas
- **Home Assistant es el centro de los protocolos.** Ya trae KNX, Zigbee (ZHA), Matter, Z-Wave, Modbus, MQTT y
  ESPHome, y Sonoff por SonoffLAN (HACS). El Estudio no programa conectores propios por protocolo.
- **El Estudio aporta lo suyo:** catálogo y nombres, dónde corre cada función, gemelo digital, modo cable, voz local,
  presentación y armado de cada instalación.
- **ESPHome se queda en la placa.** Tasmota trae Matter, pero quita la voz, el gemelo y el modo cable. ESPHome no tiene
  Matter oficial (noviembre de 2026; solo un componente externo muy temprano).
- La IA que entiende frases libres no cabe en el ESP32: corre en el PC o en la nube.

## Decisiones pendientes
- KNX: ¿hay instalación real (router o interfaz KNX IP) o se prepara solo con el simulador KNX Virtual?
- Matterbridge (Alexa, Google, Apple): necesita la red del equipo; en Windows con Docker Desktop no funciona bien.
  ¿Esperar a la mini PC con Debian?
- Separar en un archivo lo que habla con Home Assistant (≈2 h, opcional): solo si algún día se piensa cambiar de centro.

## Mockup
```
Estudio → Aparatos → Circuito maestro → «Dónde corre cada función»
┌──────────────────────────────────────────────────────┐
│ Función              Placa   PC    Nube   Estado     │
│ 💡 Relé «Ventilador»  (●)    ( )          ✅         │
│ ⏲ Apagar en 30 min    (●)    ( )          ✅         │
│ 🕗 Horario 19:00–23:00 (●)   ( )          ✅         │
│ 📱 Página del celular  (●)   (●)          ✅         │
│ 🎙 «Okay Nabu»         (●)   ( )          ✅         │
│ 🧠 Entender la frase    —    (●)   ( )    ✅         │
│ 🔊 Alexa / Google       ⚠    (●)          ✅         │
│──────────────────────────────────────────────────────│
│ Memoria de la placa  ███████░░░ 72 %                 │
│ Cambios sin instalar: Horario → Placa                │
│                    [Restablecer] [Aplicar ▶]         │
└──────────────────────────────────────────────────────┘
 Aplicar: Compilando… → Instalando por Wi-Fi… → ✅ Listo
 Error:   ⚠ «Matter en la placa quita la voz. Elige una.»

Estudio → Protocolos (lo que Home Assistant tiene activo)
┌ Protocolos ──────────────────────────────────────────┐
│ ✅ ESPHome   1 placa                 [Abrir en HA ↗]  │
│ ✅ MQTT      placa por cable         [Abrir en HA ↗]  │
│ ⬜ KNX       necesita router KNX IP  [Añadir en HA ↗] │
│ ⬜ Zigbee    necesita adaptador USB  [Añadir en HA ↗] │
│ ⬜ Sonoff    SonoffLAN (HACS)        [Añadir ▶]       │
└──────────────────────────────────────────────────────┘

Página de la placa en el celular (sin PC)
┌ Circuito maestro ───────┐
│ Ventilador       [ ● ]  │
│ Apagar en  [30] min     │
│ Pantalla  [Hola    ] ✓  │
│ ⚠ PC sin conexión:      │
│   funciones locales OK  │
└─────────────────────────┘
```

## Ejemplos de uso
| Situación | Qué pasa |
|---|---|
| «Okay nabu, apaga la luz del salón» (KNX) | La placa escucha, el PC entiende la frase y Home Assistant manda la orden por KNX. |
| Se apaga el PC | Botón, horario y página del celular siguen en la placa; la pantalla OLED dice «Sin motor». |
| Se cae el Wi-Fi | La placa sigue en Home Assistant por el cable USB (modo cable). |
| Pasar el horario de PC a placa | El Estudio incluye su paquete, compila e instala por Wi-Fi. |
| Cliente con edificio KNX | Se añade KNX en Home Assistant con sus direcciones de grupo; la voz y el celular ya lo manejan. |
| Presentación al jefe | «▶ Presentación»: gemelo, cable, protocolos y «dónde corre cada función» (escenas 6 a 9). |

## Fases
0. **Presentación** (hecho): escenas 6 a 9 en `web/studio/presentations/jefe.json`. Lo que funciona se enseña; lo que
   viene se dice como lo siguiente.
1. **Placa autónoma (≈3 h):** `packages/web_server.yaml` (página con usuario y clave en los secretos),
   `packages/local_rules.yaml` (botón → relé sin red, apagado por tiempo, horario con NTP) y aviso «Sin motor» en la
   pantalla cuando Home Assistant no responde.
2. **Catálogo de funciones (≈1 día):** `catalog/functions/*.json` con esquema: lugares posibles, paquete o servicio de
   cada lugar, memoria aproximada y conflictos. Validador puro en `studio/domain/`, pruebas sin placa. Bloque «Dónde
   corre cada función» y compilar con los paquetes elegidos (`serve_firmware.py` ya compila).
3. **Protocolos (≈medio día + demo KNX 2–3 h):** bloque «Protocolos» que lee las integraciones activas de Home
   Assistant y abre su pantalla para añadir una. Demo KNX con KNX Virtual (la persona usuaria crea la cuenta en knx.org
   y lo descarga). SonoffLAN con instalación automática (HACS).
4. **Módulos:** según `docs/planes/sistema_modulos.md`; cada función y cada protocolo llegan como módulo.

## Capas y archivos
- Dominio: catálogo de funciones y validador (lugares, memoria, conflictos) en `studio/domain/`.
- Aplicación: caso de uso «aplicar lugares» (qué paquetes compilar, qué servicios activar).
- Infraestructura: paquetes de `firmware/esphome/packages/`, `serve_firmware.py`, cliente de Home Assistant.
- Presentación: bloques en `web/studio/js/blocks/`, textos en `web/locales/es.json`.

## Licencias y costes
- Home Assistant y sus integraciones: Apache 2.0. ESPHome: MIT y GPL (el firmware se entrega con su código).
- KNX: los aparatos se configuran con **ETS**, de pago (la versión gratuita es limitada). KNX Virtual es gratuito.
- Matter: un aparato propio sin certificar funciona, pero Alexa y Google avisan de «no certificado».
- Tasmota: GPL-3.0 (descartado para esta placa).
- SonoffLAN: MIT, por HACS (comunidad, no oficial).

## Hasta dónde escala
Varias placas: cada una con su propia elección de lugares y su firmware. Edificios: Home Assistant con KNX o Modbus y
áreas por planta. Lo primero que se rompe: la memoria de cada placa (el validador lo avisa) y un solo Home Assistant
para muchos edificios; ahí se pasa a un Home Assistant por edificio y el Estudio los lista.

## Verificación
- Sin placa: pruebas del validador (memoria y conflictos) y del armado de paquetes.
- Con la placa: apagar el PC y comprobar botón, horario y página del celular; volver a encenderlo y comprobar la voz.
- KNX: «apaga la luz del salón» mueve la luz de KNX Virtual.
