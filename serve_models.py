# AI model choice for the Studio page: lists the models each AI offers and saves the chosen one, then runs the
# Home Assistant setup so its assistant uses it. Local models come from Ollama (only those that can use tools, which
# is how the AI controls the devices); cloud models come from ai_providers.json.
# list_models(secrets_dir, provider_id) -> (status, payload);  set_model(secrets_dir, provider_id, model) -> (status, payload).
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from serve_ai import _providers, _run_setup

ROOT = Path(__file__).resolve().parent
OLLAMA_URL = os.environ.get("OLLAMA_HOST_URL", "http://127.0.0.1:11434")
DEFAULT_LOCAL_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:4b")
EQUIPMENT_FILE = ROOT / "catalog" / "equipment" / f"{os.environ.get('STUDIO_EQUIPMENT', 'laptop-demo')}.json"
MODELS_FILE = "ai_models.json"  # in the secrets folder, next to ai_keys.json: setup_ha.py reads it there


def _chosen(secrets_dir: Path) -> dict:
    path = secrets_dir / MODELS_FILE
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _write_chosen(secrets_dir: Path, chosen: dict) -> None:
    secrets_dir.mkdir(parents=True, exist_ok=True)
    (secrets_dir / MODELS_FILE).write_text(json.dumps(chosen, indent=2), encoding="utf-8")


def _gpu_gb() -> float | None:
    try:
        return json.loads(EQUIPMENT_FILE.read_text(encoding="utf-8")).get("gpu_vram_gb")
    except (OSError, ValueError):
        return None


def _ollama_models() -> list:
    with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=10) as reply:
        tags = json.loads(reply.read())["models"]
    return [{"id": m["name"], "label": m["name"], "sizeGb": round(m["size"] / 1e9, 1)}
            for m in tags if "tools" in m.get("capabilities", ["tools"])]


def _models(provider: dict) -> list:
    if provider["cloud"]:
        return [{"id": m, "label": m, "sizeGb": None} for m in provider.get("models", [])]
    return _ollama_models()


def list_models(secrets_dir: Path, provider_id: str) -> tuple[int, dict]:
    provider = next((p for p in _providers() if p["id"] == provider_id), None)
    if not provider:
        return 404, {"code": "E_PROVIDER", "message": "Esa IA no existe."}
    try:
        models = _models(provider)
    except (urllib.error.URLError, OSError, KeyError, ValueError) as err:
        return 502, {"code": "E_OLLAMA_DOWN", "message": f"No responde Ollama en {OLLAMA_URL}. ¿Está abierto? ({err})"}
    default = None if provider["cloud"] else DEFAULT_LOCAL_MODEL  # None = the provider's recommended model
    return 200, {"models": models, "current": _chosen(secrets_dir).get(provider_id, default),
                 "gpuGb": None if provider["cloud"] else _gpu_gb()}


def set_model(secrets_dir: Path, provider_id: str, model: str) -> tuple[int, dict]:
    status, listing = list_models(secrets_dir, provider_id)
    if status != 200:
        return status, listing
    if model not in {m["id"] for m in listing["models"]}:
        return 400, {"code": "E_MODEL", "message": "Ese modelo no está en la lista. Recarga la página."}
    chosen = _chosen(secrets_dir)
    previous = chosen.get(provider_id)
    chosen[provider_id] = model
    _write_chosen(secrets_dir, chosen)
    result = _run_setup(secrets_dir, provider_id)
    if not result["ok"]:  # the model HA could not use is not kept: the previous one stays
        if previous:
            chosen[provider_id] = previous
        else:
            chosen.pop(provider_id)
        _write_chosen(secrets_dir, chosen)
        _run_setup(secrets_dir, provider_id)
        return 400, {**result, "current": previous}
    return 200, {**result, "current": model}
