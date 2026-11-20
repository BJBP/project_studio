# External connections, pure: checks a connection against its connector's option schema, and the rule that only one
# connection may give orders to a device. check_all(connections, connectors) -> [issue]; with_defaults(conn, connector).
# connection = {id, name, type, enabled, options: {...}, devices: [{entity_id, remote_id, direction: send|both}]}.
import re

ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
REMOTE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")  # safe inside an MQTT topic or a URL path
ENTITY_RE = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")
DIRECTIONS = ("send", "both")


def with_defaults(conn: dict, connector: dict) -> dict:
    options = {o["key"]: o.get("default") for o in connector.get("options", [])}
    return {**conn, "options": {**options, **(conn.get("options") or {})}}


def _option_issues(conn: dict, connector: dict) -> list:
    issues = []
    for option in connector.get("options", []):
        value = conn["options"].get(option["key"])
        if value in (None, ""):
            if option.get("required"):
                issues.append({"code": "E_CONN_OPTION", "connection": conn["id"], "option": option["key"]})
            continue
        if option.get("type") == "number":
            ok = isinstance(value, (int, float)) and option.get("min", value) <= value <= option.get("max", value)
        else:
            ok = isinstance(value, str) and len(value) <= option.get("max_length", 255)
        if not ok:
            issues.append({"code": "E_CONN_OPTION", "connection": conn["id"], "option": option["key"]})
    return issues


def _device_issues(conn: dict) -> list:
    issues, seen = [], set()
    for device in conn.get("devices", []):
        ok = (ENTITY_RE.match(str(device.get("entity_id", ""))) and REMOTE_RE.match(str(device.get("remote_id", "")))
              and device.get("direction") in DIRECTIONS and device["remote_id"] not in seen)
        if not ok:
            issues.append({"code": "E_CONN_DEVICE", "connection": conn["id"], "device": str(device.get("entity_id", ""))})
        seen.add(device.get("remote_id"))
    return issues


def check_connection(conn: dict, connectors: dict) -> list:
    if not ID_RE.match(str(conn.get("id", ""))) or not str(conn.get("name", "")).strip():
        return [{"code": "E_CONN_FIELDS", "connection": str(conn.get("id", ""))}]
    connector = connectors.get(conn.get("type"))
    if not connector:
        return [{"code": "E_CONN_TYPE", "connection": conn["id"], "type": str(conn.get("type", ""))}]
    return _option_issues(with_defaults(conn, connector), connector) + _device_issues(conn)


def check_all(connections: list, connectors: dict) -> list:
    issues = [i for conn in connections for i in check_connection(conn, connectors)]
    ids = [c.get("id") for c in connections]
    issues += [{"code": "E_CONN_DUPLICATE", "connection": i} for i in sorted({i for i in ids if ids.count(i) > 1})]
    commanders: dict = {}
    for conn in connections:
        for device in conn.get("devices", []):
            if device.get("direction") == "both":
                commanders.setdefault(device.get("entity_id"), []).append(conn.get("id"))
    issues += [{"code": "E_CONN_COMMANDS", "device": entity, "connections": ", ".join(owners)}
               for entity, owners in commanders.items() if len(owners) > 1]
    return issues
