# Plan: Estudio de proyectos abiertos (domótica con voz local, videoportero, industrial)

## Contexto
Hoy existe `Downloads\proyectos\tutorial_circuito_3d\tutorial_circuito_3d.html` (2152 líneas, Three.js r128):
un tutorial 3D para armar un ESP32-S3 con micrófono INMP441, amplificador MAX98357A, buzzer, OLED, relé 12V y
cámara USB. Los 5 modos solo encienden relé/buzzer 3,6 s (`runProjectSim`, línea ~1881).

Objetivo: demostrar al jefe que soluciones como Alexa, videoporteros o monitoreo industrial se construyen
**solo con software abierto, protocolos abiertos e IA local**, y que la empresa las puede **instalar y vender a
clientes**. Para eso, un programa (el **Estudio**) que:
- maneja **proyectos** (domótica, videoportero, industrial…) y deja elegir entre ellos;
- muestra la **arquitectura** de cada proyecto y deja **cambiar piezas** (p. ej. Home Assistant → openHAB),
  con su licencia y los avisos de compatibilidad;
- muestra el **flujo de negocio** completo: comprar → armar → probar → instalar → entregar → soporte;
- incluye el **tutorial paso a paso** (para quien no sabe electrónica) y la **simulación** de lo que aún no se tiene.

Decisiones del usuario: base Home Assistant para domótica; voz completa sin hardware primero; cambiar una
pieza = **ver y planificar** (solo domótica se instala de verdad al principio); flujo = **guía con listas por
etapa** (facturas e inventario, más adelante con un ERP abierto).

Equipo comprobado: Docker Desktop, Ollama nativo, RTX 3050 4 GB, 16 GB RAM, Python con `uv`, Node.

## Qué existe ya (para no construirlo)
- Plataformas: Home Assistant (Apache 2.0), openHAB (EPL-2.0), Node-RED (Apache 2.0), ThingsBoard CE
  (Apache 2.0), OpenRemote (AGPL ⚠️). Entran como **alternativas del catálogo**, no se programan.
- Inventario/ERP: InvenTree (MIT), Odoo Community (LGPL), ERPNext (GPLv3): integración futura del flujo.
- Diagramas: se dibujan con SVG propio a partir del JSON (sin librería); Mermaid (MIT) es la alternativa.
- No hay un programa abierto que junte catálogo de piezas + licencias + arquitectura + flujo de instalación
  para integradores: esa parte es la propia, y es pequeña porque todo sale de datos.

## Modelo de datos (JSON con esquema; añadir algo = añadir datos, no código)
- **Pieza** (`catalog/components/<id>.json`): tipo (software/hardware), **huecos** que puede ocupar (`hub`,
  `broker`, `stt`, `llm`, `tts`, `firmware`, `video`, `sip`, `historian`, `dashboard`…), **protocolos** que habla
  (`mqtt`, `wyoming`, `esphome-api`, `sip`, `rtsp`, `modbus`, `opc-ua`…), licencia (SPDX, uso comercial:
  sí / con condiciones / no, notas), si es instalable (fragmento de Docker), enlace a su documentación.
- **Proyecto** (`projects/<id>/project.json`): nombre, sector, huecos → pieza elegida, conexiones entre huecos
  con su protocolo, lista de hardware (pieza + cantidad), etapas del flujo con sus listas, tutorial asociado,
  documentos a entregar.
- **Reglas del dominio**: al cambiar una pieza se comprueba que siga hablando los protocolos de sus conexiones
  («openHAB no habla Wyoming: la voz necesita otra pieza puente») y se recalcula la tabla de licencias del
  proyecto (alerta si alguna es «no comercial» o AGPL).
- Los datos reales de la empresa y sus clientes van en una carpeta aparte (`project_studio_data\`, con su repo,
  `AGENTS.md` y backlog). El repo trae solo **3 proyectos de ejemplo neutros**:
  1. **Domótica con voz local** (funciona): Home Assistant + Mosquitto + Whisper + Piper + Ollama + ESP32/ESPHome.
  2. **Videoportero IP** (simulado): ESP32-S3 con cámara o cámara IP, Asterisk (GPLv2) / FreeSWITCH (MPL),
     Frigate (MIT) para video, aviso al móvil vía Home Assistant.
  3. **Monitoreo industrial** (simulado): sensores Modbus/OPC-UA, Node-RED, ThingsBoard CE, InfluxDB OSS (MIT),
     Grafana (AGPL ⚠️, se explica la condición).

## Mockups
Inicio:
```
┌ Estudio ─────────────────────────────────────┐
│ Proyectos                     [+ Nuevo]      │
│ ┌ 🏠 Domótica voz ┐┌ 🚪 Videoportero┐┌ 🏭 Indus┐│
│ │ ● funciona      ││ ◐ simulado     ││ ◐ simul.││
│ │ 6 piezas · ✓lic ││ 5 piezas · ⚠1  ││ ⚠ AGPL  ││
│ └─────────────────┘└────────────────┘└─────────┘│
│ Vacío: «Crea tu primer proyecto desde un ejemplo»│
└──────────────────────────────────────────────┘
```
Proyecto → pestañas `Arquitectura | Flujo | Tutorial 3D | Demo | Licencias`:
```
┌ 🏠 Domótica voz ─ [Arquitectura] Flujo  Tutorial  Demo  Licencias ┐
│  [Micrófono]─audio─►[Whisper]─texto─►[ Hub ]─HTTP─►[ IA ]          │
│  [ESP32]──esphome-api──────────────►[Home  ]◄─mqtt─[Mosquitto]     │
│  [Parlante]◄─audio──[Piper]◄─texto──[Assist]                       │
│ ┌ Hueco: Hub ───────────────────────────┐                          │
│ │ Pieza: [Home Assistant ▾]  Apache 2.0 ✓│                         │
│ │  alternativas: openHAB · Node-RED · …  │                         │
│ │ ⚠ openHAB no habla «wyoming» (voz)     │  (foco: borde azul)     │
│ └────────────────────────────────────────┘                         │
└────────────────────────────────────────────────────────────────────┘
```
Flujo:
```
 Comprar ─► Armar ─► Probar ─► Instalar ─► Entregar ─► Soporte
 ☑ ESP32-S3 ×1   ☐ Paso 1..13 (abre el tutorial 3D)
 ☑ INMP441  ×1   ☐ «✅ Pruébalo» de cada pieza
 ☐ Relé 5V  ×1   Entregar: [⬇ licencias.md] [⬇ manual] [⬇ firmware]
 Progreso 3/18 ▮▮▯▯▯▯▯▯
```
Demo (domótica): mantener 🎤 → «enciende el foco» → el foco 3D se enciende, la OLED virtual y el parlante
virtual responden. Sin permiso de micrófono: «⌨️ Escribir la orden».

## Ejemplos de uso
- Doble clic en `iniciar_estudio.bat` → tarjeta «Domótica voz» → «Demo» → hablarle.
- Pestaña Arquitectura → hueco «Hub» → elegir openHAB → aparece el aviso de compatibilidad y la tabla de
  licencias cambia; «Restablecer» vuelve a Home Assistant.
- «+ Nuevo» → desde «Videoportero» → se copia a la carpeta de datos con otro nombre para un cliente.
- Agente / automatización: `studio check <datos> domotica-voz` → `OK` o `E_PROTOCOL_MISMATCH hub wyoming`;
  `studio export <datos> domotica-voz --docs` → `licencias.md`, `THIRD_PARTY_NOTICES.md`, lista de compras CSV.

## Guion de la demo para el jefe (~8 min, va en `docs/demo_jefe.md`)
1. Inicio del Estudio: tres proyectos, todos con piezas abiertas.
2. Demo de voz con el Wi-Fi apagado: «enciende el foco», «¿está abierta la puerta?». Todo corre en la laptop.
3. Arquitectura: cambiar Home Assistant por openHAB. El Estudio dice qué se rompe y cómo cambian las licencias.
4. Videoportero e industrial: otros sectores con las mismas piezas y los mismos protocolos.
5. Flujo: la lista de compras, el tutorial 3D, la prueba de cada pieza y los documentos para el cliente.
6. Licencias: qué se puede vender, qué hay que entregar y qué se evita.
7. Cierre: coste por cliente sin cuotas y siguiente paso (prototipo real, fase 4).

### Presentación automática (el Estudio se presenta solo)
- Botón «▶ Presentación» en Inicio. El Estudio recorre las escenas solo: cambia de pantalla, resalta lo que
  explica, habla con una voz local, muestra subtítulos y ejecuta las acciones de verdad. Por ejemplo, manda la
  frase «enciende el foco», ya grabada, por el mismo canal de voz, y el foco 3D se enciende de verdad.
- El guion es un JSON con esquema (`presentations/<id>.json`): escenas con pantalla, texto narrado, elemento
  resaltado, acción y pausa. Cada proyecto y cada cliente puede tener el suyo, editable sin tocar el código.
- Es el mismo motor que el recorrido guiado de la Ayuda (obligatorio en todo programa): se construye una vez.
- Controles: ⏸ pausa · ⏮ ⏭ escena · 🔇 sin voz (solo subtítulos) · velocidad · Esc para salir. Si el jefe
  pregunta algo, se pausa y se le habla al asistente en vivo.
- Si una acción falla (p. ej. Home Assistant apagado), la escena lo dice, se salta y la presentación sigue.
- Voz: en la fase 1, texto + subtítulos con la voz local de Windows (sin red); desde la fase 2, Piper
  (la misma voz del asistente). Exportar la presentación como video: backlog.
```
┌──────────────────────────────────────────────┐
│ (pantalla del Estudio, con la pieza resaltada)│
│        ┌──────────┐                           │
│        │ Hub ◄────┼── «Podemos cambiar…»      │
│        └──────────┘                           │
├──────────────────────────────────────────────┤
│ 💬 «No estamos atados a un proveedor…»        │
│ ⏮ ⏸ ⏭  Escena 3/7 ▮▮▮▯▯▯▯  🔇  1x   [Esc]   │
└──────────────────────────────────────────────┘
```

### Equipos: laptop y mini PC
- Cada proyecto declara sus **equipos**, que son las computadoras donde corre. Los ejemplos traen dos perfiles neutros:
  - **Laptop de desarrollo y demo** (la actual: GPU de 4 GB, 16 GB RAM).
  - **Mini PC del cliente**: CPU x86 de 4 núcleos, 16 GB RAM, SSD, sin GPU, encendida siempre y con Linux + Docker.
- Cada pieza del catálogo declara lo que necesita (RAM, CPU, GPU opcional). Una regla del dominio comprueba
  si cabe en el equipo y recomienda la variante: en la mini PC sin GPU, Whisper `base-int8` y un LLM de
  1–2 mil millones de parámetros (`qwen3:1.7b`); en la laptop con GPU, `qwen3:4b`. Muestra el tiempo de
  respuesta esperado.
- Reparto recomendado: **todo en la mini PC del cliente**, que sigue funcionando sin internet y sin la laptop.
  La laptop sirve para desarrollar, para la demo y para instalar. Otros repartos (p. ej. la IA en un equipo
  más potente de la red) se pueden elegir en Arquitectura.
- **Instalar en la mini PC** desde el Estudio: pantalla «Equipos» → «Preparar mini PC» genera un paquete
  (`docker-compose.yml`, configuración, `instalar.sh`) que se copia por USB o por la red (SSH) y se ejecuta allí.
  Lo mismo para las copias de seguridad y las actualizaciones.
- Estado del equipo en el Estudio: encendido, servicios en marcha, espacio libre, última copia de seguridad.
```
┌ Equipos ─ 🏠 Domótica voz ────────────────────┐
│ 💻 Laptop demo     ● en marcha  IA: qwen3:4b   │
│ 🖥️ Mini PC cliente ○ sin preparar              │
│    16 GB · sin GPU → IA: qwen3:1.7b (~3 s)     │
│    [Preparar mini PC] [⬇ Paquete USB]          │
│ ⚠ «Ollama qwen3:4b no cabe sin GPU: lento»     │
└────────────────────────────────────────────────┘
```

- **Decisión del usuario:** por ahora todo corre en **esta laptop**. La mini PC aparece solo como opción a
  mostrar, en «Equipos», con su perfil, sus avisos de recursos y en la lista de compras. No se instala.

### Marcas, modelos y lista de compras
- Cada pieza de hardware tiene sus **modelos concretos**: marca, modelo o código de pieza, especificación clave
  y compatibilidad con el proyecto (p. ej. «ESP32-S3 con 8 MB de PSRAM: sí»; «ESP32 clásico: no sirve para la voz»).
  Cada modelo lleva sus **ofertas**: tienda, enlace, precio, moneda y fecha del precio. Se marca el modelo «probado» (el que ya se tiene)
  y los «alternativos».
- **Conflicto con la regla del repo neutro:** marcas, tiendas y precios no van en el repositorio. Se resuelve así:
  el repo trae la especificación genérica de cada pieza (qué debe cumplir); los modelos, tiendas y precios van en
  la carpeta de datos (`project_studio_data\catalog\`), local. El Estudio los junta en pantalla.
- La carpeta de datos se llena al empezar con los modelos que el tutorial ya usa: ESP32-S3-WROOM-1 N16R8,
  INMP441, MAX98357A, OLED SSD1306 0.96" bicolor, relé SRD-05VDC-SL-C, fuente 12V 2A, cooler 8025 12V,
  foco 12V, protoboard MB-102. Se añaden 2–3 mini PC candidatas buscadas en la web en ese momento. **Los precios no se inventan:**
  quedan «a completar», o se buscan en tiendas que el usuario indique.
- Pestaña **Compras** del proyecto: cantidades × número de unidades («1 demo + 3 clientes»), agrupado por
  tienda, total por moneda, piezas ya compradas ☑, y **exportar** la lista (CSV y PDF) para hacer el pedido
  de una vez. Aviso si un modelo elegido no cumple la especificación de su pieza.
```
┌ Compras ─ 🏠 Domótica voz ─ unidades: [4 ▾] ────────────┐
│ Pieza        Modelo (marca)           Cant  Tienda  Precio│
│ ESP32-S3     WROOM-1 N16R8 ✓probado    4    …       a compl│
│ Micrófono    INMP441 ✓probado          4    …       …      │
│ Mini PC      (elige) ▾ 3 candidatas    1    …       …      │
│ ☑ comprado: 2/9      Total: — (faltan precios)            │
│ [⬇ CSV] [⬇ PDF]   ⚠ «ESP32 clásico no sirve para voz»     │
└───────────────────────────────────────────────────────────┘
```

### Configurar el ESP32 desde el Estudio
- Pantalla «Aparatos» del proyecto: cada ESP32 con su nombre, habitación, piezas que lleva y estado.
- «⚡ Instalar firmware»: con el cable USB, desde el navegador (ESP Web Tools, Apache 2.0, por Web Serial).
  Sin Arduino IDE ni programas aparte. El firmware se arma con las piezas que lleva ese aparato (`base` + `oled` +
  `relay` …), y los pines salen del tutorial.
- «📶 Wi-Fi»: el nombre y la clave de la red se escriben una sola vez y se envían por **Improv Serial**
  (estándar abierto). La clave se guarda en los secretos del equipo, nunca en el repo.
- Después aparece solo en Home Assistant (adopción de ESPHome) con su nombre y área. Las actualizaciones
  siguientes van por Wi-Fi (OTA), con el panel de ESPHome en el stack.
- «✅ Probar»: los mismos «Pruébalo» del tutorial, pieza por pieza, con «Qué deberías ver» y «Si no funciona».
```
┌ Aparatos ─ 🏠 Domótica voz ──────────────────┐
│ 📟 asistente-taller  Taller   ● en línea v1.2 │
│    piezas: oled relay buzzer mic speaker      │
│    [⚡ Instalar] [📶 Wi-Fi] [✅ Probar] [↻ OTA]│
│ 📟 (nuevo)  [+ Añadir ESP32]                  │
│ Sin cable: «Conecta el USB en el puerto UART» │
└───────────────────────────────────────────────┘
```

### Interfaz de bloques, minimalista (regla general en `Agents/AGENTS.md`)
- Cada pestaña es una banda de **bloques movibles**: «Circuito 3D», «OLED», «Conversación», «Micrófono»,
  «Aparatos», «Cámara», «Arquitectura», «Compras»… Cada bloque tiene su ⚙ con sus opciones (p. ej. OLED:
  tamaño, mostrar franja; Micrófono: dispositivo, sensibilidad; Conversación: mostrar tiempos).
- Por defecto, la Demo muestra solo 3 bloques: Circuito 3D, OLED y Hablar. El resto está en «+ Añadir bloque».
- Administrador de bloques: mostrar/ocultar, arrastrar o mover con botones/teclado, «Restablecer». La disposición
  se guarda en `layout.json` en la carpeta de datos y vuelve al abrir.
- Es un motor común (`web/engines/blocks/`) que usan todas las pestañas; se construye en la fase 1.
```
┌ Demo ───────────────────────────── [+ Añadir bloque] [⟲] ┐
│ ┌ Circuito 3D ─────────── ⚙ ✕ ┐ ┌ OLED ──────── ⚙ ✕ ┐     │
│ │      (vista 3D)              │ │ FOCO: ON          │     │
│ │                              │ │ Listo, encendido  │     │
│ └──────────────────────────────┘ └───────────────────┘     │
│ ┌ Hablar ───────────────────────────────────── ⚙ ✕ ┐       │
│ │ [🎤 Mantén para hablar]  ▮▮▮▯▯  [⌨️ Escribir]      │       │
│ └──────────────────────────────────────────────────┘       │
│ ⠿ = arrastrar · ⚙ = ajustes del bloque · ✕ = ocultar        │
└────────────────────────────────────────────────────────────┘
```

## Arquitectura del Estudio (cebolla)
```
project_studio/
  studio/domain/         project.py, component.py, compatibility.py, licenses.py, lifecycle.py  (puro)
  studio/application/    list_projects, swap_component, check_project, export_docs, toggle_checklist
                         puertos: ProjectRepository, CatalogRepository, DocExporter
  studio/infrastructure/ json_repository.py (+ validación con jsonschema), markdown_exporter.py
  studio/presentation/   api.py (FastAPI, MIT) · cli.py (códigos de error) · web/ (HTML+JS sin framework)
  web/tutorials/circuito_3d/   el tutorial 3D actual (copia; el original no se toca hasta aprobar)
  web/demos/voice/             js/domain|application|infrastructure|presentation (ESP32 virtual, mic/amp virtuales)
  stack/domotica-voz/          docker-compose.yml, ha-config/, mosquitto/, setup_ha.py
  firmware/esphome/            packages/{base,oled,relay,buzzer,mic,speaker,voice}.yaml + circuito_maestro.yaml
  catalog/ · examples/projects/ · schemas/ · locales/es.json · tests/
  Dockerfile · docker-compose.yml · iniciar_estudio.bat/.sh · AGENTS.md · docs/
```
- `tests/test_layers.py` (y `tests/layers.test.mjs` para el JS) fallan si una capa interior importa una exterior.
- Textos de interfaz en `locales/es.json` (español por defecto). Puertos solo en 127.0.0.1.
- El ESP32 virtual y los aparatos simulados se anuncian en Home Assistant por MQTT Discovery con los mismos
  nombres que tendrá el ESP32 real con ESPHome: pasar de simulado a real no cambia frases ni automatizaciones.

## Licencias y venta a otras empresas
- Se puede cobrar por instalar, configurar, vender hardware, soporte y automatizaciones a medida.
- MIT / Apache / BSD: se conserva el aviso. GPLv3 (firmware ESPHome, Piper): al entregar el aparato se entrega
  el código del firmware. AGPL (Grafana, OpenRemote): si se modifica y se ofrece por red, se publica el cambio.
- Modelos: Qwen3-4B (Apache 2.0) ✓; Qwen2.5-3B (no comercial) ✗; modelos de openWakeWord (CC BY-NC-SA) ✗,
  se usa microWakeWord (Apache 2.0); cada voz de Piper se revisa una por una.
- Marcas: «basado en Home Assistant», nunca como nombre propio. Las licencias no dan garantía: la da la empresa.
- Cámaras y micrófonos: protección de datos. 220 V: electricista autorizado.
- Todo esto vive en los datos del catálogo, y el Estudio lo muestra y lo exporta por proyecto.

## Fases (se muestra cada una antes de seguir)
(Orden decidido por el usuario: **primero la demo de voz**.)
1. **Demo de voz de tu circuito**: Estudio mínimo (solo la tarjeta «Domótica voz» y su pestaña Demo, con el
   3D del tutorial). Stack Docker (Home Assistant, Mosquitto, Whisper, Piper) + Ollama `qwen3:4b`,
   `setup_ha.py` automático, ESP32 virtual por MQTT con relé foco, relé cooler, buzzer y texto OLED.
   OLED virtual a 128×64 con franja amarilla/azul (igual que la real), micrófono/parlante virtuales con
   vúmetro, «⌨️ Escribir la orden», lanzador `iniciar_estudio.bat`, Docker. El tutorial 3D actual sigue
   funcionando igual.
2. **Estudio completo**: catálogo + 3 proyectos de ejemplo, Inicio, Arquitectura (cambiar pieza con avisos y
   licencias), Compras con marcas y modelos, Flujo con listas, Licencias, «Equipos» (laptop + mini PC como
   perfil); `studio check/export`; motor de recorridos (Ayuda + «▶ Presentación», con la escena de voz).
3. **Simulación ampliada**: aparatos simulados en `devices.json` (puerta, temperatura, cerradura…), cámara con
   detección de movimiento, los 5 modos como automatizaciones de Home Assistant.
4. **Hardware real + tutorial**: firmware ESPHome por piezas, pantalla «Aparatos» (instalar por USB, Wi-Fi
   por Improv, probar, OTA), «✅ Pruébalo» por pieza en el tutorial 3D, pasos nuevos «Instalar ESPHome»,
   «Conectar a Home Assistant» y «Hablarle».
4b. **Mini PC (solo cuando se compre)**: paquete de instalación para Linux y copias de seguridad. Hasta entonces,
   «Equipos» la muestra como perfil y aviso de recursos (fase 2). Todo corre en la laptop.
5. **Videoportero e industrial simulados** con su demo, y la integración del flujo con InvenTree/Odoo.
Pendiente de cada fase → `docs/backlog.md`; administrador de bandas movibles en el Estudio → fase 1 si cabe, si no backlog.

## Verificación
- Fase 1: `docker compose up -d`; `curl 127.0.0.1:8123/api/` con token → 200; `tests/e2e_voice.mjs`: Piper
  genera «enciende el foco», se manda a Home Assistant y se comprueba por MQTT que el relé virtual está en ON;
  pruebas de dominio con Node (mensajes de Discovery, texto OLED que cabe en 128×64); navegador integrado:
  pestaña Demo, orden escrita, captura con el foco encendido y la OLED, consola sin errores.
- Fase 2: `uv run pytest` (compatibilidad, licencias, compras, progreso; capas); `studio check` en los 3
  ejemplos; `curl 127.0.0.1:<puerto>/api/projects` → 200; captura al cambiar Hub a openHAB.
- Fase 4: `esphome config` y `esphome compile` en Docker. Flasheo y voz en el aparato real: backlog.

## Coste y forma de trabajo
- Trabajo grande: se aprueba y se hace **fase por fase**. Fase 1 es lo que el jefe ve primero.
- Según `~/.agents/equipo.md`, cada fase se parte en tareas cortas para Hermes (un archivo + su prueba),
  revisadas por mí antes de la siguiente. Planes, decisiones y todo lo que toca secretos (token de Home
  Assistant en `~/.agents/secrets/`) no se delegan.
- Descargas (fase 1): imágenes Docker ~2 GB, `qwen3:4b` ~2,6 GB, modelo Whisper y voz Piper.
- El plan se guarda en `docs/planes/estudio_proyectos.md` del repo nuevo.

## Riesgos
- Alcance amplio: el riesgo principal es abrir todo y no terminar nada; por eso solo Domótica funciona de verdad
  al principio y el resto es datos + simulación.
- 4 GB de VRAM: respuesta de voz 2–5 s; si va lento, `qwen3:1.7b`.
- Las licencias del catálogo se escriben a mano: se cita la fuente de cada una y se revisan antes de un contrato
  grande (no es asesoría legal).
