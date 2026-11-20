# Plan: submódulos e instalación de módulos por zip

Estado: fase 1 hecha (2026-11-20); fase 2 pendiente.

## Para qué
Todo es un módulo. Un módulo puede tener **submódulos** (`"parent": "<id>"`): «Conexiones externas» es un módulo y cada
conector es un submódulo suyo. Los módulos que no trae el programa se instalan **desde un archivo .zip** en la pantalla
Módulos, se actualizan con otro zip y se desinstalan con un botón. Así se pasan a otra persona sin copiar carpetas.

## Decisiones aprobadas
- `parent` cuenta como requisito: sin el padre activo, el submódulo queda inactivo; el padre no se apaga ni se
  desinstala mientras tenga submódulos activos.
- Módulos incluidos: `modules/` del programa (no se desinstalan). Instalados: `<datos>/modules/<id>/` (al instalar
  quedan activos). Un id incluido no se puede reemplazar con un zip.
- Un conector = submódulo de `conexiones` con `adds.connector` (`type`, `transport`, `options`) y `translate.py`.
  «Conexiones externas» ofrece los conectores de sus submódulos activos.
- Revisión del zip antes de instalar: máximo 2 MB comprimido y 5 MB descomprimido, 200 archivos, sin rutas que salgan
  de su carpeta, un solo `module.json` (en la raíz o en una carpeta), manifiesto válido. Errores `E_EXT_*`.
- Dos pasos: «revisar» (muestra nombre, versión, licencia, padre, qué añade y la versión que reemplaza) e «instalar».
- Aviso fijo: un módulo es código que el Estudio ejecuta.

## Mockup
```
┌ Módulos ─────────────── [📦 Instalar o actualizar (.zip)] ┐
│ 🌐 Conexiones externas   incluido  v1.0  MIT  [✓ activo]  │
│   └ 🏙 MQTT de ejemplo   instalado v1.0  MIT  [✓ activo]  │
│                                        [Desinstalar]       │
│ 🔗 Protocolos            incluido  v1.0  MIT  [✓ activo]  │
└────────────────────────────────────────────────────────────┘
 Al elegir el zip:
   ✓ 🏙 MQTT de ejemplo v1.0 · MIT · submódulo de «Conexiones externas»
     Añade: tipo de conexión «MQTT de ejemplo» · Reemplaza: v0.9
   ⚠ Es código que el Estudio ejecuta. Instala solo de quien confíes.
   [Instalar]  [Cancelar]
 Error: ⚠ El zip no trae module.json (E_EXT_NO_MANIFEST).
```
En «Conexiones externas», «➕ Instalar un conector (.zip)» lleva a esta pantalla.

## Ejemplos
- Doble clic en `empaquetar.bat` del repositorio de un conector → `<id>-<versión>.zip`.
- Módulos → Instalar → elegir el zip → Instalar → el tipo aparece en «+ Añadir conexión».
- `python -m studio modules <datos> install conector.zip` / `uninstall <id>` (para agentes).

## Capas
- dominio: `studio/domain/modules.py` (parent, conector), `studio/domain/packages.py` (revisión del zip, pura).
- aplicación: `studio/application/modules.py` (inspect, install, uninstall).
- infraestructura: `module_store.py` (incluidos + instalados, extraer, borrar), `connection_store.py` (conectores
  desde módulos activos).
- presentación: rutas `/api/studio/modules/inspect|install|<id>/uninstall`, `modules-screen.js`, CLI.

## Fases
1. Submódulos, instalados en datos, zip para módulos sin pantalla propia (conectores). ← hecha
2. Módulos instalados con bloques propios (servir su JavaScript desde la carpeta de datos).

## Hasta dónde escala
Decenas de módulos y submódulos; la lista en árbol se lee bien hasta unos 50. Después: buscador y plegar ramas.
Sin firma, no se sabe quién hizo un zip: firmar extensiones queda para después.

## Verificación
Pruebas de reglas y del instalador (zips sanos, dañados, con rutas trampa, con `\` en los nombres). En el navegador:
el zip real del conector se revisó, se instaló y quedó como submódulo; al apagarlo la conexión se paró y al
encenderlo volvió, y la plataforma volvió a encender y apagar el foco real.
