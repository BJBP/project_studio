# Adds the integrations (MQTT, Wyoming STT/TTS/wake word, Ollama) and builds Spanish voice pipelines in Home Assistant.
# Receives an authenticated HaClient; idempotent: what already exists is left as it is.
import json
import os
import time
from pathlib import Path

from ha_client import HaClient, HaError

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434")
LANGUAGE = os.environ.get("VOICE_LANGUAGE", "es")
TIME_ZONE = os.environ.get("HA_TIME_ZONE", "UTC")
VOICE_FILE = Path(os.environ.get("STUDIO_SECRETS", Path.home() / ".agents" / "secrets" / "project_studio")) / "voice.json"


def chosen_wake_word() -> str:
    """The word picked in the Studio page (voice.json, next to the keys); otherwise WAKE_WORD or okay_nabu."""
    saved = json.loads(VOICE_FILE.read_text(encoding="utf-8")) if VOICE_FILE.exists() else {}
    return saved.get("wake_word") or os.environ.get("WAKE_WORD", "okay_nabu")

INTEGRATIONS = [
    ("mqtt", {"broker": {"broker": "mosquitto", "port": 1883, "protocol": "5",
                         "other_settings": {"set_client_cert": False, "set_ca_cert": "off", "transport": "tcp"}}}, "mosquitto"),
    ("wyoming", {"user": {"host": "whisper", "port": 10300}}, "whisper"),
    ("wyoming", {"user": {"host": "piper", "port": 10200}}, "piper"),
    ("wyoming", {"user": {"host": "wakeword", "port": 10400}}, "microWakeWord"),
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
    needed = ("stt.", "tts.piper", "wake_word.")
    deadline = time.time() + timeout_s
    while True:
        states = client.get("/api/states")
        ids = [s["entity_id"] for s in states]
        if all(any(i.startswith(n) for i in ids) for n in needed) or time.time() > deadline:
            return states
        time.sleep(3)


def known_wake_words(client: HaClient, entity: str) -> list:
    return client.ws({"type": "wake_word/info", "entity_id": entity})[0]["wake_words"]


def reload_wake_detector(client: HaClient, entity: str, timeout_s: int = 30) -> list:
    """A newly imported word is only known after HA reloads the detector's integration."""
    entry = next(e for e in client.get("/api/config/config_entries/entry")
                 if e["domain"] == "wyoming" and "microWakeWord" in e["title"])
    client.post(f"/api/config/config_entries/entry/{entry['entry_id']}/reload")
    deadline = time.time() + timeout_s
    while True:
        try:
            return known_wake_words(client, entity)
        except HaError:  # the entity is briefly missing while it reloads
            if time.time() > deadline:
                raise
            time.sleep(2)


def wake_word_fields(client: HaClient, states: list) -> dict:
    """The wake word detector and its word, so the browser can start a run by voice ("okay nabu")."""
    entity = find_entity(states, "wake_word")
    wanted = chosen_wake_word()
    words = known_wake_words(client, entity)
    if not any(w["id"] == wanted for w in words):
        words = reload_wake_detector(client, entity)
    if not any(w["id"] == wanted for w in words):
        raise HaError("E_WAKE_WORD", f"El detector no conoce «{wanted}». Disponibles: {', '.join(w['id'] for w in words)}")
    return {"wake_word_entity": entity, "wake_word_id": wanted}


def ensure_pipeline(client: HaClient, name: str, conversation_engine: str, preferred: bool = False) -> None:
    """One voice pipeline per AI: the wake word starts it, Whisper hears, the AI answers, Piper speaks."""
    states = wait_for_entities(client)
    wake = wake_word_fields(client, states)
    pipelines = client.ws({"type": "assist_pipeline/pipeline/list"})[0]
    existing = next((p for p in pipelines["pipelines"] if p["name"] == name), None)
    # prefer_local_intents: simple orders ("enciende el foco") run in HA itself; the AI answers the rest.
    if existing:  # older setups lack local intents or the wake word: update them in place
        if existing.get("prefer_local_intents") and existing.get("wake_word_id") == wake["wake_word_id"]:
            return
        fields = {k: v for k, v in existing.items() if k != "id"}
        client.ws({"type": "assist_pipeline/pipeline/update", "pipeline_id": existing["id"],
                   **fields, **wake, "prefer_local_intents": True})
        return
    created = client.ws({
        "type": "assist_pipeline/pipeline/create", "name": name, "language": LANGUAGE,
        "conversation_engine": conversation_engine, "conversation_language": LANGUAGE,
        "stt_engine": find_entity(states, "stt"), "stt_language": LANGUAGE,
        "tts_engine": find_entity(states, "tts", "piper"), "tts_language": "es_ES", "tts_voice": None,
        **wake, "prefer_local_intents": True,
    })[0]
    if preferred:
        client.ws({"type": "assist_pipeline/pipeline/set_preferred", "pipeline_id": created["id"]})
