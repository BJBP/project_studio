# Adds the integrations (MQTT, Wyoming STT/TTS, Ollama) and builds Spanish voice pipelines in Home Assistant.
# Receives an authenticated HaClient; idempotent: what already exists is left as it is.
import os
import time

from ha_client import HaClient, HaError

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434")
LANGUAGE = os.environ.get("VOICE_LANGUAGE", "es")
TIME_ZONE = os.environ.get("HA_TIME_ZONE", "UTC")

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
        if result.get("type") == "form" and result.get("errors"):
            raise HaError("E_FLOW_INVALID", f"{handler}: Home Assistant rechazó los datos ({result['errors']}). "
                                            "Si es una clave de IA, revisa que esté bien copiada.")
    if result.get("type") == "abort" and result.get("reason") not in ("already_configured", "single_instance_allowed"):
        raise HaError("E_FLOW_ABORT", f"{handler}: {result.get('reason')}")
    return result


def ensure_integrations(client: HaClient) -> None:
    entries = client.get("/api/config/config_entries/entry")
    for handler, answers, marker in INTEGRATIONS:
        exists = any(e["domain"] == handler and (marker in e["title"] or handler == "mqtt") for e in entries)
        if not exists:
            run_flow(client, handler, answers)


def ensure_core_config(client: HaClient) -> None:
    client.ws({"type": "config/core/update", "time_zone": TIME_ZONE, "unit_system": "metric", "language": LANGUAGE})


def find_entity(states: list, domain: str, hint: str = "") -> str:
    ids = [s["entity_id"] for s in states if s["entity_id"].startswith(domain + ".") and hint in s["entity_id"]]
    if not ids:
        raise HaError("E_ENTITY_MISSING", f"No hay entidad {domain}.*{hint}*. ¿Arrancaron whisper/piper/ollama?")
    return ids[0]


def wait_for_entities(client: HaClient, timeout_s: int = 90) -> list:
    """New integrations create their entities a few seconds after the flow ends."""
    needed = ("stt.", "tts.piper")
    deadline = time.time() + timeout_s
    while True:
        states = client.get("/api/states")
        ids = [s["entity_id"] for s in states]
        if all(any(i.startswith(n) for i in ids) for n in needed) or time.time() > deadline:
            return states
        time.sleep(3)


def ensure_pipeline(client: HaClient, name: str, conversation_engine: str, preferred: bool = False) -> None:
    """One voice pipeline per AI: Whisper hears, the AI answers, Piper speaks."""
    states = wait_for_entities(client)
    pipelines = client.ws({"type": "assist_pipeline/pipeline/list"})[0]
    existing = next((p for p in pipelines["pipelines"] if p["name"] == name), None)
    if existing and existing.get("prefer_local_intents"):
        return
    if existing:  # older setups created it without local intents: switch them on
        fields = {k: v for k, v in existing.items() if k != "id"}
        client.ws({"type": "assist_pipeline/pipeline/update", "pipeline_id": existing["id"],
                   **fields, "prefer_local_intents": True})
        return
    # prefer_local_intents: simple orders ("enciende el foco") run in HA itself; the AI answers the rest.
    created = client.ws({
        "type": "assist_pipeline/pipeline/create", "name": name, "language": LANGUAGE,
        "conversation_engine": conversation_engine, "conversation_language": LANGUAGE,
        "stt_engine": find_entity(states, "stt"), "stt_language": LANGUAGE,
        "tts_engine": find_entity(states, "tts", "piper"), "tts_language": "es_ES", "tts_voice": None,
        "wake_word_entity": None, "wake_word_id": None, "prefer_local_intents": True,
    })[0]
    if preferred:
        client.ws({"type": "assist_pipeline/pipeline/set_preferred", "pipeline_id": created["id"]})
