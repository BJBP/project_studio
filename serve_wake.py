# Wake word choice for the Studio page: lists the words the detector knows (built in + own trained ones), saves the
# chosen one and imports a trained word (.json + .tflite from any microWakeWord trainer) into the data folder.
# list_words(secrets_dir, words_dir) -> (status, payload);  set_word(...) and import_word(...) -> (status, payload).
import base64
import binascii
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from serve_ai import _run_setup

# Words bundled in the rhasspy/wyoming-microwakeword image (pymicro_wakeword/models).
BUILT_IN = {"okay_nabu": "Okay Nabu", "hey_jarvis": "Hey Jarvis", "hey_mycroft": "Hey Mycroft", "alexa": "Alexa"}
DEFAULT_WORD = os.environ.get("WAKE_WORD", "okay_nabu")
DETECTOR_CONTAINER = os.environ.get("WAKEWORD_CONTAINER", "domotica-voz-wakeword-1")
VOICE_FILE = "voice.json"  # in the secrets folder, next to ai_keys.json: setup_ha.py reads it there
MAX_MODEL_BYTES = 2_000_000
MAX_NAME_CHARS = 40
TFLITE_MAGIC = b"TFL3"  # bytes 4-8 of every TensorFlow Lite model


def _chosen(secrets_dir: Path) -> str:
    path = secrets_dir / VOICE_FILE
    saved = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return saved.get("wake_word") or DEFAULT_WORD


def _save_chosen(secrets_dir: Path, word: str) -> None:
    secrets_dir.mkdir(parents=True, exist_ok=True)
    (secrets_dir / VOICE_FILE).write_text(json.dumps({"wake_word": word}, indent=2), encoding="utf-8")


def _own_words(words_dir: Path) -> dict:
    found = {}
    for config in sorted(words_dir.glob("*.json")) if words_dir.exists() else []:
        try:
            data = json.loads(config.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if data.get("type") == "micro" and (words_dir / str(data.get("model", ""))).exists():
            found[config.stem] = data.get("wake_word", config.stem)
    return found


def list_words(secrets_dir: Path, words_dir: Path) -> tuple[int, dict]:
    words = [{"id": i, "name": n, "own": False} for i, n in BUILT_IN.items()]
    words += [{"id": i, "name": n, "own": True} for i, n in _own_words(words_dir).items() if i not in BUILT_IN]
    return 200, {"words": words, "current": _chosen(secrets_dir)}


def set_word(secrets_dir: Path, words_dir: Path, word: str) -> tuple[int, dict]:
    known = {w["id"] for w in list_words(secrets_dir, words_dir)[1]["words"]}
    if word not in known:
        return 400, {"ok": False, "code": "E_WAKE_WORD", "message": "Esa palabra no está en la lista. Recarga la página."}
    previous = _chosen(secrets_dir)
    _save_chosen(secrets_dir, word)
    result = _run_setup(secrets_dir, "local")
    if not result["ok"]:  # a word HA could not use is not kept
        _save_chosen(secrets_dir, previous)
        return 400, {**result, "current": previous}
    return 200, {**result, "current": word}


def _word_id(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def import_word(words_dir: Path, config_text: str, model_b64: str) -> tuple[int, dict]:
    """Validates the trainer's two files and stores them as <id>.json + <id>.tflite; then restarts the detector."""
    try:
        config = json.loads(config_text)
        model = base64.b64decode(model_b64, validate=True)
    except (ValueError, binascii.Error):
        return 400, {"ok": False, "code": "E_WAKE_FILES", "message": "Los archivos no son válidos: elige el .json y el .tflite del entrenador."}
    name = str(config.get("wake_word", "")).strip() if isinstance(config, dict) else ""
    word_id = _word_id(name)
    if config.get("type") != "micro" or not word_id or len(name) > MAX_NAME_CHARS:
        return 400, {"ok": False, "code": "E_WAKE_FILES", "message": "El .json no es de microWakeWord (falta «type: micro» o «wake_word»)."}
    if model[4:8] != TFLITE_MAGIC or len(model) > MAX_MODEL_BYTES:
        return 400, {"ok": False, "code": "E_WAKE_FILES", "message": "El .tflite no es un modelo válido o pesa más de 2 MB."}
    if word_id in BUILT_IN:
        return 400, {"ok": False, "code": "E_WAKE_EXISTS", "message": f"«{name}» ya viene con el detector."}
    words_dir.mkdir(parents=True, exist_ok=True)
    (words_dir / f"{word_id}.tflite").write_bytes(model)
    (words_dir / f"{word_id}.json").write_text(json.dumps({**config, "model": f"{word_id}.tflite"}, indent=2), encoding="utf-8")
    restarted = _restart_detector()
    message = f"«{name}» importada." if restarted else f"«{name}» guardada. Reinicia el stack de voz para usarla."
    return 200, {"ok": True, "code": None if restarted else "E_DETECTOR_RESTART", "message": message, "id": word_id}


def _restart_detector() -> bool:
    """The detector reads its words only when it starts. In Docker the Studio has no docker command: it asks the
    restart-only proxy (DOCKER_HOST=tcp://docker-proxy:2375) through the Docker API."""
    proxy = os.environ.get("DOCKER_HOST", "")
    try:
        if proxy.startswith("tcp://"):
            url = f"http://{proxy.removeprefix('tcp://')}/containers/{DETECTOR_CONTAINER}/restart"
            with urllib.request.urlopen(urllib.request.Request(url, method="POST"), timeout=60) as reply:
                return reply.status == 204
        return subprocess.run(["docker", "restart", DETECTOR_CONTAINER], capture_output=True, timeout=60).returncode == 0
    except (OSError, subprocess.TimeoutExpired, urllib.error.URLError):
        return False
