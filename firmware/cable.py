# Cable mode, pure: the "@" text lines the board speaks on its «COM» connector (firmware serial_bridge) and the Home
# Assistant MQTT messages that stand in for the board while it has no Wi-Fi. No serial port, no network here.
# Lines: PC -> board "@get" | "@set\tname\tvalue" | "@wifi\tssid\tpassword"; board -> PC "@state\tdomain\tname\tvalue",
# "@wifi\t1|0\tip", "@error\twhat". Entities: <domain>.<device>_cable_<key>, named as chosen in «Qué hay conectado».
# Voice: PC -> board "@voice\t1|0", "@stop", "@play\trate", "@spk\tbase64", "@end"; board -> PC "@listen", "@mic\tbase64".
import base64
import json

GET_LINE = b"@get\n"
STOP_LINE = b"@stop\n"
END_LINE = b"@end\n"
LISTEN_LINE = b"@listen\n"  # talk now, without the wake word
HA_MISSES_FOR_CABLE = 3  # Wi-Fi reports in a row (~15 s) in which Home Assistant cannot see the board
SPK_CHUNK = 1536  # PCM bytes per @spk line: 2 KB of base64, under the board's 4 KB line limit
FORBIDDEN = ("\t", "\n", "\r")
CABLE_KINDS = ("switch", "button", "text")  # what the bridge can move; sensors (mic level) stay Wi-Fi only


def _line(*parts: str) -> bytes:
    if any(c in str(p) for p in parts for c in FORBIDDEN):
        raise ValueError("E_LINE_FORMAT")
    return ("\t".join(parts) + "\n").encode("utf-8")


def set_line(name: str, value: str) -> bytes:
    return _line("@set", name, value)


def wifi_line(ssid: str, password: str) -> bytes:
    return _line("@wifi", ssid, password)


def cable_needed(board_online: bool, ha_misses: int) -> bool:
    """The cable takes over when the board has no Wi-Fi, and also when it believes it has but Home Assistant has not
    reached it for a while (a stuck Wi-Fi link: the board keeps its IP but nothing gets through)."""
    return not board_online or ha_misses >= HA_MISSES_FOR_CABLE


def voice_line(on: bool) -> bytes:
    return _line("@voice", "1" if on else "0")


def play_line(sample_rate: int) -> bytes:
    return _line("@play", str(int(sample_rate)))


def speaker_lines(pcm: bytes) -> list:
    """The answer's 16-bit mono PCM as @spk lines."""
    return [_line("@spk", base64.b64encode(pcm[i:i + SPK_CHUNK]).decode("ascii")) for i in range(0, len(pcm), SPK_CHUNK)]


def parse(raw: bytes) -> dict | None:
    """One board line -> {"kind": "state"|"wifi"|"error", ...}; None for normal log lines."""
    line = raw.decode("utf-8", errors="replace").strip("\r\n")
    start = line.find("@")  # the logger may print a colour code first
    parts = line[start:].split("\t") if start >= 0 else []
    if parts[:1] == ["@state"] and len(parts) == 4:
        return {"kind": "state", "domain": parts[1], "name": parts[2], "value": parts[3]}
    if parts[:1] == ["@wifi"] and len(parts) == 3:
        return {"kind": "wifi", "online": parts[1] == "1", "ip": parts[2] or None}
    if parts[:1] == ["@listen"]:
        return {"kind": "listen"}
    if parts[:1] == ["@mic"] and len(parts) == 2:
        try:
            return {"kind": "mic", "pcm": base64.b64decode(parts[1], validate=True)}
        except ValueError:
            return None  # a line broken by a log line in the middle: that bit of audio is lost
    if parts[:1] == ["@error"] and len(parts) >= 2:
        return {"kind": "error", "message": parts[1]}
    return None


def _topics(base: str, device_id: str, key: str) -> dict:
    root = f"{base}/{device_id}_cable"
    return {"command": f"{root}/{key}/set", "state": f"{root}/{key}/state", "availability": f"{root}/status"}


def entities(device: dict) -> list:
    """Catalog entities the cable can carry."""
    return [e for e in device.get("entities", []) if e["component"] in CABLE_KINDS]


def entity_for(device: dict, domain: str, name: str) -> dict | None:
    """Catalog entity for a board line (the board reports its firmware names: "Foco", "Pantalla"...)."""
    return next((e for e in entities(device) if e["component"] == domain and e["name"] == name), None)


def discovery(base: str, device: dict, names: dict) -> list:
    """[(topic, payload)] that announce the cable stand-in in Home Assistant (retained)."""
    found = []
    for item in entities(device):
        topics = _topics(base, device["id"], item["key"])
        payload = {
            "name": names.get(item["key"]) or item["name"],
            "unique_id": f"{device['id']}_cable_{item['key']}",
            "default_entity_id": f"{item['component']}.{device['id']}_cable_{item['key']}",
            "command_topic": topics["command"], "availability_topic": topics["availability"],
            "device": {"identifiers": [f"{device['id']}_cable"], "name": f"{device['name']} (cable)",
                       "manufacturer": "Project Studio cable"},
        }
        if item["component"] != "button":
            payload["state_topic"] = topics["state"]
        if item["component"] == "text":
            payload["max"] = item.get("max", 64)
        found.append((f"homeassistant/{item['component']}/{device['id']}_cable/{item['key']}/config", json.dumps(payload)))
    return found


def removal(device: dict) -> list:
    """[(topic, "")]: empty retained configs take the stand-in out of Home Assistant (Wi-Fi is back)."""
    return [(f"homeassistant/{e['component']}/{device['id']}_cable/{e['key']}/config", "") for e in entities(device)]


def state_message(base: str, device: dict, line: dict) -> tuple | None:
    """(topic, payload) for a "@state" line, or None (buttons have no state; unknown names are ignored)."""
    item = entity_for(device, line["domain"], line["name"])
    if not item or item["component"] == "button":
        return None
    value = line["value"].upper() if item["component"] == "switch" else line["value"]
    return _topics(base, device["id"], item["key"])["state"], value


def command_line(base: str, device: dict, topic: str, payload: str) -> bytes | None:
    """The "@set" line for a Home Assistant command, or None if the topic is not ours."""
    for item in entities(device):
        if topic == _topics(base, device["id"], item["key"])["command"]:
            value = payload.lower() if item["component"] == "switch" else payload
            return set_line(item["name"], value)
    return None


def availability_topic(base: str, device: dict) -> str:
    return f"{base}/{device['id']}_cable/status"


def entity_ids(device: dict, via_cable: bool) -> list:
    """The board's Wi-Fi entities, or their cable stand-ins: only one set is shown to the voice assistant."""
    middle = "_cable_" if via_cable else "_"
    return [f"{e['component']}.{device['id']}{middle}{e['key']}" for e in entities(device)]


def voice_aliases(device: dict, names: dict) -> list:
    """[(cable entity_id, alias)]: Home Assistant calls the stand-in "<device> (cable) <name>"; the alias lets the
    voice find it by the plain name, as device_names.py does for the Wi-Fi board."""
    return [(entity_id, names.get(e["key"]) or e["name"])
            for entity_id, e in zip(entity_ids(device, via_cable=True), entities(device))]
