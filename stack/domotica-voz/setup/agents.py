# Sets up one voice assistant per AI listed in ai_providers.json: the local one always, each cloud one once its key
# is saved. Receives an authenticated HaClient; idempotent. Keys live outside the repo (ai_keys.json in the secrets).
import json
import os
import time
from pathlib import Path

from flows import ensure_pipeline, run_flow
from ha_client import HaClient, HaError

PROVIDERS_FILE = Path(__file__).resolve().parent.parent / "ai_providers.json"
SECRETS_DIR = Path(os.environ.get("STUDIO_SECRETS", Path.home() / ".agents" / "secrets" / "project_studio"))
KEYS_FILE = SECRETS_DIR / "ai_keys.json"
MODELS_FILE = SECRETS_DIR / "ai_models.json"  # model chosen per AI in the Studio page (serve_models.py)
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:4b")
PROMPT_END = ("Controlas los aparatos que tienes disponibles. "
              "Responde en español, en una sola frase corta y natural, sin emojis ni formato.")
PROMPT_LOCAL = ("Eres el asistente de voz de este lugar. Funcionas por completo en este equipo, sin internet y sin "
                "nube: nunca digas que usas la nube. " + PROMPT_END)
PROMPT_CLOUD = ("Eres el asistente de voz de este lugar. Piensas con {label}, un servicio de IA en la nube; "
                "los aparatos se controlan en este equipo. " + PROMPT_END)


def load_providers() -> list:
    return json.loads(PROVIDERS_FILE.read_text(encoding="utf-8"))["providers"]


def load_keys() -> dict:
    return json.loads(KEYS_FILE.read_text(encoding="utf-8")) if KEYS_FILE.exists() else {}


def load_models() -> dict:
    return json.loads(MODELS_FILE.read_text(encoding="utf-8")) if MODELS_FILE.exists() else {}


def agent_options(provider: dict, model: str | None = None) -> dict:
    if not provider["cloud"]:
        return {"model": model or OLLAMA_MODEL, "think": False, "prompt": PROMPT_LOCAL, "llm_hass_api": ["assist"]}
    options = {"recommended": True, "prompt": PROMPT_CLOUD.format(label=provider["label"]), "llm_hass_api": ["assist"]}
    if model:  # a chosen cloud model turns off the provider's recommended settings
        options.update({"recommended": False, provider.get("model_option", "chat_model"): model})
    return options


def ensure_entry(client: HaClient, provider: dict, key: str | None) -> dict | None:
    """The provider's HA integration; created with the saved key when it does not exist yet."""
    entries = [e for e in client.get("/api/config/config_entries/entry") if e["domain"] == provider["integration"]]
    if entries or not provider["cloud"]:
        return entries[0] if entries else None
    if not key:
        return None
    run_flow(client, provider["integration"], {provider["key_step"]: {"api_key": key}})
    return next(e for e in client.get("/api/config/config_entries/entry") if e["domain"] == provider["integration"])


def ensure_agent(client: HaClient, entry: dict, provider: dict, model: str | None = None) -> None:
    """Integrations keep their conversation agents as sub-entries: one with our prompt and control of the house."""
    subs = client.ws({"type": "config_entries/subentries/list", "entry_id": entry["entry_id"]})[0]
    current = next((s for s in subs if s.get("subentry_type") == "conversation"), None)
    options = agent_options(provider, model)
    start = {"handler": [entry["entry_id"], "conversation"], "show_advanced_options": False}
    if current:
        start.update({"source": "reconfigure", "subentry_id": current["subentry_id"]})
    else:
        options["name"] = provider["label"]
    flow = client.post("/api/config/config_entries/subentries/flow", start)
    flow = client.post(f"/api/config/config_entries/subentries/flow/{flow['flow_id']}", options)
    if flow.get("type") not in ("create_entry", "abort"):
        raise HaError("E_AGENT", f"{provider['label']}: no se configuró el agente ({flow.get('errors') or flow})")


def conversation_entity(client: HaClient, provider: dict, timeout_s: int = 60) -> str:
    """The agent's entity appears a few seconds after the integration is set up."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        registry = client.ws({"type": "config/entity_registry/list"})[0]
        ids = [r["entity_id"] for r in registry
               if r["platform"] == provider["integration"] and r["entity_id"].startswith("conversation.")]
        if ids:
            return ids[0]
        time.sleep(3)
    raise HaError("E_ENTITY_MISSING", f"{provider['label']}: no aparece su agente de conversación en Home Assistant.")


def ensure_assistants(client: HaClient) -> tuple[list, dict]:
    """Returns (labels of ready assistants, {provider id: problem}). A cloud AI that fails never blocks the rest."""
    keys, models, ready, problems = load_keys(), load_models(), [], {}
    for provider in load_providers():
        try:
            entry = ensure_entry(client, provider, keys.get(provider["id"]))
            if not entry:
                continue
            ensure_agent(client, entry, provider, models.get(provider["id"]))
            ensure_pipeline(client, provider["pipeline"], conversation_entity(client, provider),
                            preferred=not provider["cloud"])
            ready.append(provider["label"])
        except HaError as err:
            if not provider["cloud"]:
                raise
            problems[provider["id"]] = str(err)
    return ready, problems
