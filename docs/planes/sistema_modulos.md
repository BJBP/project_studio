# Sistema de módulos (todo lo visible y cada función se instala y se quita)

## Estado
Propuesta (2026-11-19). **Decisión del usuario: pendiente.** Nada construido. Para retomarlo, elegir entre el corte
pequeño (núcleo + barra + avisos, ~0,5 días) y la fase 1 completa.

## Qué cambia
Hoy las pestañas del proyecto están fijas en `web/studio/js/project.js` y la cabecera (Presentación, Ayuda) en
`index.html`. Con el sistema de módulos, el Estudio queda en un **núcleo mínimo** que lee qué módulos están activos y
los carga. Todo lo demás es un módulo: la barra de navegación, el panel de avisos, el inicio, cada pestaña, cada
bloque, cada conexión con otro programa (ESPConnect, Frigate…), un idioma o un tema visual.

## Antes de construir: qué existe
| Opción | Licencia | Qué aporta | Por qué no se usa entera |
|---|---|---|---|
| single-spa (microfrontends) | MIT | cargar apps dentro de otra | pensada para varios frameworks; aquí sobra |
| Backstage (sistema de plugins) | Apache 2.0 | plugins de interfaz y servidor | React + Node, muy pesado para este proyecto |
| Módulos ES del navegador (`import()`) | estándar | cargar un archivo de módulo cuando hace falta | **se usa**: sin dependencias |
| Docker Compose `include` y perfiles | Apache 2.0 | añadir servicios desde otro archivo | **se usa** para los módulos con servicio |

Recomendación: núcleo propio pequeño (unas 150 líneas) sobre `import()` y Compose. No hace falta otra librería.

## Mockup: administrador «Módulos» (Ajustes → Módulos)
```
┌ 🧩 Módulos ─────────────────────── [+ Instalar] ┐
│ Buscar: [________]  Mostrar: (Todos ▾)         │
│ ┌──────────────────────────────────────────────┐ │
│ │ 🧭 Barra de navegación   1.0  MIT   [● Activo]│ │
│ │    Añade: barra superior   núcleo ✔          │ │
│ ├──────────────────────────────────────────────┤ │
│ │ 🔔 Panel de avisos       1.0  MIT   [● Activo]│ │
│ ├──────────────────────────────────────────────┤ │
│ │ 🔧 ESPConnect            0.1  MIT   [○ Apagado]│
│ │    Añade: servicio Docker, botón en Aparatos  │ │
│ │    [Activar]  [Desinstalar]  [⚙]             │ │
│ └──────────────────────────────────────────────┘ │
│ Estado vacío: «No hay módulos. Instala uno.»    │
│ Error: «⚠ ESPConnect necesita Docker. Ábrelo y   │
│         vuelve a probar.» [Reintentar]          │
└─────────────────────────────────────────────────┘
```

Confirmación al instalar (muestra qué añade antes de aceptar):
```
┌ Instalar «ESPConnect» ─────────────────┐
│ Licencia: MIT (uso comercial: sí)       │
│ Añade: servicio esp-connect (Docker),   │
│        botón «🔧 Administrar placa»      │
│ Necesita: módulo «Aparatos»             │
│          [Cancelar]  [Instalar]         │
└────────────────────────────────────────┘
```

Desinstalar: «Se quitan sus botones, pestañas y servicio. Tus datos se quedan. ☐ Borrar también sus datos».

## Manifiesto `modules/<id>/module.json`
```json
{
  "id": "esp-connect", "name": "ESPConnect", "version": "0.1.0", "license": "MIT",
  "icon": "🔧", "requires": ["devices"],
  "adds": {
    "slots":    [{ "slot": "devices.actions", "entry": "web/button.js" }],
    "tabs":     [],
    "blocks":   [],
    "services": "compose.yml",
    "routes":   null,
    "locales":  "locales/"
  },
  "options": [{ "key": "port", "type": "number", "default": 5174 }]
}
```
- **Ranuras (slots)**: los sitios declarados donde un módulo pone algo: `shell.nav`, `shell.notifications`,
  `home`, `project.tabs`, `devices.actions`… Añadir una ranura es añadir un nombre; no hay `if` por módulo.
- **Contrato con el núcleo** (lo único que ve un módulo): `register({ addTab, addBlock, fill(slot, render),
  notify(text, level), navigate(hash), on(event, fn) })`. Una barra de navegación nueva solo tiene que cumplirlo.

## Dónde se guarda
- Los módulos que trae el programa: `modules/` del repo (las 8 pestañas de hoy, la barra, los avisos, la Ayuda).
- Qué está instalado y activo, y sus opciones: `../project_studio_data/modules.json` (datos del usuario).
- Los módulos instalados desde una carpeta o un `.zip`: `../project_studio_data/modules/<id>/`.

## Capas
| Capa | Qué va |
|---|---|
| Dominio (`studio/domain/modules.py`) | validar el manifiesto, orden por dependencias, detectar ciclos y faltantes |
| Aplicación (`studio/application/modules.py`) | casos de uso: listar, instalar, activar, desactivar, desinstalar; puerto `ModuleStore` y `ServiceRunner` |
| Infraestructura | `modules.json` en disco, copia de carpetas o `.zip`, `docker compose` para servicios |
| Presentación | `python -m studio modules …`, rutas `/api/modules`, núcleo web `web/core/`, pantalla «Módulos» |

## Ejemplos de uso
- Con clics: Ajustes → Módulos → «ESPConnect» → Activar. Aparece «🔧 Administrar placa» en Aparatos.
- Con clics: Módulos → «Barra de navegación» → Desactivar; se activa «Barra lateral» y el resto sigue igual.
- Agente: `uv run --no-project python -m studio modules enable esp-connect` → `OK: esp-connect activo` o
  `E_MODULE_REQUIRES: falta el módulo devices. Actívalo primero.`
- Agente: `... modules install ruta/a/mi_modulo.zip` → valida el manifiesto y lo copia a la carpeta de datos.

Códigos de error: `E_MODULE_MANIFEST`, `E_MODULE_REQUIRES`, `E_MODULE_CYCLE`, `E_MODULE_EXISTS`,
`E_MODULE_NOT_FOUND`, `E_MODULE_SERVICE` (Docker no arrancó el servicio).

## Fases
1. **Núcleo y pantalla «Módulos»** (~1,5 días). Manifiesto, dominio y casos de uso con pruebas; núcleo web que
   carga módulos y ranuras; las 8 pestañas, la barra de navegación, la Ayuda y la Presentación pasan a módulos
   del repo; nuevo módulo «Panel de avisos»; pantalla «Módulos» con activar y desactivar; comando `modules`.
   Se ve igual que hoy, pero todo se puede apagar y encender.
2. **Servidor por módulos** (~1 día). `serve_ai`, `serve_models`, `serve_wake` y `serve_firmware` declaran sus
   rutas en su módulo; `serve.py` queda en el núcleo que las une.
3. **Servicios e instalación desde fuera** (~1 día). `compose.yml` por módulo con Compose `include`; instalar
   desde carpeta o `.zip` con la confirmación del mockup; desinstalar. Primer módulo externo: ESPConnect.

## Verificación
- Pruebas de dominio y casos de uso (manifiesto, dependencias, ciclos, desinstalar sin borrar datos).
- Prueba de capas (`tests/studio/test_layers.py`) ampliada a `modules`.
- Navegador: desactivar la barra y los avisos y ver que el resto funciona; volver a activarlos; sin errores de consola.
- Las 78 pruebas de Node y las de Python actuales siguen pasando.

## Hasta dónde escala
Decenas de módulos sin cambios. Lo primero que se rompe con cientos es la pantalla (hace falta buscar y agrupar
por tipo, ya previsto en el mockup) y el arranque (cada módulo se carga solo cuando su ranura se muestra).
Las versiones se comparan solo como «igual o mayor»; rangos de versión, cuando haya módulos de terceros.

## Riesgos
- Un módulo de terceros ejecuta código (JS en la página, Python en el servidor): se instala solo desde una carpeta
  o `.zip` que elige el usuario, con la confirmación que muestra licencia y lo que añade.
- Mover las pestañas a módulos toca `project.js`, `main.js` e `index.html`: se hace en la fase 1 con las pruebas
  actuales como red.

## Decisiones pendientes
- ¿El estado de los módulos en la carpeta de datos (recomendado) o por equipo?
- ¿Empezar por la fase 1 completa, o primero un corte más pequeño (núcleo + barra + avisos, ~0,5 días)?
