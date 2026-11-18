# Palabra para despertar: elegir, importar y entrenar

## Decisiones aprobadas (2026-11-18)
- Fase A: elegir entre las palabras del detector (Okay Nabu, Hey Jarvis, Hey Mycroft, Alexa) e importar una palabra
  entrenada (`.json` + `.tflite` de cualquier entrenador de microWakeWord). Las palabras propias van en la carpeta de
  datos (`project_studio_data/wake_words/`), no en el repositorio.
- Fase B: entrenar desde el Estudio con el entrenador de TaterTotterson (Docker con NVIDIA, AGPL-3.0, usado como
  programa aparte y sin modificar). Espera a que haya ~40 GB libres; hoy hay 15 GB y la GPU es de 4 GB.
- Licencias: los sonidos de fondo del entrenamiento (FMA, FSD50K, WHAM!) incluyen material no comercial según sus
  fuentes. Antes de vender una palabra entrenada a un cliente hay que revisarlo (no es asesoría legal).

## Mockup
```
┌ 🎙️ Hablar ─────────────────────── ⚙ ✕ ┐
│ Palabra: [ Okay Nabu            ▾ ]    │
│ [📥 Importar palabra] [🎓 Entrenar]    │  (Entrenar: fase B)
│ [👂 Activar por voz]                   │
│ 👂 Esperando «oye casa»…               │
│ ⚠ E_WAKE_FILES: Elige los dos archivos │  (error)
└────────────────────────────────────────┘
```

## Ejemplos de uso
- Elegir «Hey Jarvis» → unos segundos después «Hey Jarvis, enciende el foco» funciona.
- Entrenar «Oye Casa» (Colab o el entrenador) → «📥 Importar palabra» con los dos archivos → «Oye Casa (propia)».
- Sin la página: `curl -X POST /api/wake-word/import` con `{config, model(base64)}` y `POST /api/wake-word` con `{word}`.

## Piezas
| Capa | Archivo |
|---|---|
| Stack | `docker-compose.yml`: el servicio `wakeword` monta `WAKE_WORDS_DIR` en `/custom` |
| Configuración | `setup/flows.py`: lee `voice.json` y recarga el detector si no conoce la palabra |
| Servidor | `serve_wake.py` (listar, elegir, importar; valida el `.json` y la firma `TFL3` del `.tflite`) |
| Navegador | `infrastructure/wake-words.js`, `application/wake-word-choice.js`, `blocks/wake-word-picker.js` |

## Estado
- **Fase A hecha el 2026-11-18.** Comprobado: importar una palabra de prueba («Oye Prueba», hecha con el modelo de
  Okay Nabu), elegirla en la página y despertarla por voz (`voice_pipeline.py --wake`), con el foco encendido.
  Errores de archivos en la página. Se borró la palabra de prueba y se volvió a «Okay Nabu».
- Hallazgo: con la voz española de Piper, «Hey Jarvis» no despierta (tampoco la original): la prueba automática
  solo sirve para palabras que Piper pronuncia bien.
- **Fase B: pendiente** (disco).
