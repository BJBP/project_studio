# Adds the integrations (MQTT, Wyoming STT/TTS, Ollama) and the Spanish voice pipeline to Home Assistant.
# Receives an authenticated HaClient; idempotent: what already exists is left as it is.
import os
import time

from ha_client import HaClient, HaError

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:4b")
LANGUAGE = os.environ.get("VOICE_LANGUAGE", "es")
PIPELINE_NAME = "Asistente local"
TIME_ZONE = os.environ.get("HA_TIME_ZONE", "UTC")
AGENT_PROMPT = os.environ.get("AGENT_PROMPT", (
    "Eres el asistente de voz de este lugar. Funcionas por completo en este equipo, sin internet y sin nube: "
    "nunca digas que usas la nube. Controlas los aparatos que tienes disponibles. "
    "Responde en español, en una sola frase corta y natural, sin emojis ni formato."))

INTEGRATIONS = [
    ("mqtt", {"broker": {"broker": "mosquitto", "port": 1883, "protocol": "5",
                         "other_settings": {"set_client_cert": False, "set_ca_cert": "off", "transport": "tcp"}}}, "mosquitto"),
    ("wyoming", {"user": {"host": "whisper", "port": 10300}}, "whisper"),
    ("wyoming", {"user": {"host": "piper", "port": 10200}}, "piper"),
    ("ollama", {"user": {"url": OLLAMA_URL}}, OLLAMA_URL),
]


def run_flow(client: HaClient, handler: str, answers: dict) -> dict:
    result = client.post("/api/config/config_entries/flow", {"handler": handler, "show_advanced_options": False})
    while result.get("type") in ("form", "menu"):
        step = result["step_id"]
        if step not in answers:
            raise HaError("E_FLOW_STEP", f"{handler}: paso '{step}' sin respuesta prevista ({result.get('data_schema')})")
        result = client.post(f"/api/config/config_entries/flow/{result['flow_id']}", answers[step])
    if result.get("type") == "abort" and result.get("reason") not in ("already_configured", "single_instance_allowed"):
        raise HaError("E_FLOW_ABORT", f"{handler}: {result.get('reason')}")
    return result


def ensure_integrations(client: HaClient) -> None:
    entries = client.get("/api/config/config_entries/entry")
    for handler, answers, marker in INTEGRATIONS:
        exists = any(e["domain"] == handler and (marker in e["title"] or handler == "mqtt") for e in entries)
        if not exists:
            run_flow(client, handler, answers)
    ensure_ollama_agent(client)


def ensure_ollama_agent(client: HaClient) -> None:
    """Ollama keeps its conversation agents as sub-entries: one with our model and control of the house."""
    entry = next(e for e in client.get("/api/config/config_entries/entry") if e["domain"] == "ollama")
    subs = client.ws({"type": "config_entries/subentries/list", "entry_id": entry["entry_id"]})[0]
    options = {"model": OLLAMA_MODEL, "llm_hass_api": ["assist"], "think": False, "prompt": AGENT_PROMPT}
    current = next((s for s in subs if s.get("subentry_type") == "conversation"), None)
    start = {"handler": [entry["entry_id"], "conversation"], "show_advanced_options": False}
    if current:
        start.update({"source": "reconfigure", "subentry_id": current["subentry_id"]})
    else:
        options["name"] = "Ollama"
    flow = client.post("/api/config/config_entries/subentries/flow", start)
    flow = client.post(f"/api/config/config_entries/subentries/flow/{flow['flow_id']}", options)
    if flow.get("type") not in ("create_entry", "abort"):
        raise HaError("E_OLLAMA_AGENT", f"No se configuró el agente: {flow}")


def ensure_core_config(client: HaClient) -> None:
    client.ws({"type": "config/core/update", "time_zone": TIME_ZONE, "unit_system": "metric", "language": LANGUAGE})


def find_entity(states: list, domain: str, hint: str = "") -> str:
    ids = [s["entity_id"] for s in states if s["entity_id"].startswith(domain + ".") and hint in s["entity_id"]]
    if not ids:
        raise HaError("E_ENTITY_MISSING", f"No hay entidad {domain}.*{hint}*. ¿Arrancaron whisper/piper/ollama?")
    return ids[0]


def wait_for_entities(client: HaClient, timeout_s: int = 90) -> list:
    """New integrations create their entities a few seconds after the flow ends."""
    needed = ("conversation.ollama", "stt.", "tts.piper")
    deadline = time.time() + timeout_s
    while True:
        states = client.get("/api/states")
        ids = [s["entity_id"] for s in states]
        if all(any(i.startswith(n) for i in ids) for n in needed) or time.time() > deadline:
            return states
        time.sleep(3)


def ensure_pipeline(client: HaClient) -> None:
    states = wait_for_entities(client)
    pipelines = client.ws({"type": "assist_pipeline/pipeline/list"})[0]
    if any(p["name"] == PIPELINE_NAME for p in pipelines["pipelines"]):
        return
    created = client.ws({
        "type": "assist_pipeline/pipeline/create", "name": PIPELINE_NAME, "language": LANGUAGE,
        "conversation_engine": find_entity(states, "conversation", "ollama"), "conversation_language": LANGUAGE,
        "stt_engine": find_entity(states, "stt"), "stt_language": LANGUAGE,
        "tts_engine": find_entity(states, "tts", "piper"), "tts_language": "es_ES", "tts_voice": None,
        "wake_word_entity": None, "wake_word_id": None,
    })[0]
    client.ws({"type": "assist_pipeline/pipeline/set_preferred", "pipeline_id": created["id"]})
