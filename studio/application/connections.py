# External connections, use cases: list, save (add or change), delete. The store (port) keeps them in the data folder
# and knows the installed connectors and the live status the background process writes.
# Each call returns {"connectors": [...], "connections": [...], "status": {...}, "issues": [...]}.
from typing import Protocol

from studio.domain import connections as rules
from studio.application.use_cases import StudioError


class ConnectionStore(Protocol):
    def connectors(self) -> dict: ...          # {type: connector.json}
    def load(self) -> list: ...
    def save(self, connections: list) -> None: ...
    def status(self) -> dict: ...              # {connection id: {state, message, sent_at}}


def list_connections(store: ConnectionStore) -> dict:
    connectors, connections = store.connectors(), store.load()
    public = [{k: v for k, v in c.items() if not k.startswith("_")} for c in connectors.values()]  # no local paths
    return {"connectors": sorted(public, key=lambda c: c.get("name", "")),
            "connections": [rules.with_defaults(c, connectors[c["type"]]) if c.get("type") in connectors else c
                            for c in connections],
            "status": store.status(), "issues": rules.check_all(connections, connectors)}


def save_connection(store: ConnectionStore, conn: dict) -> dict:
    """Adds the connection or replaces the one with its id; refuses it (StudioError) if it has problems."""
    if not isinstance(conn, dict):
        raise StudioError("E_CONN_FIELDS", connection="")
    conn = {"enabled": True, "options": {}, "devices": [], **conn}
    others = [c for c in store.load() if c.get("id") != conn.get("id")]
    issues = rules.check_all(others + [conn], store.connectors())
    if issues:
        raise StudioError(**issues[0])
    store.save(others + [conn])
    return list_connections(store)


def delete_connection(store: ConnectionStore, connection_id: str) -> dict:
    store.save([c for c in store.load() if c.get("id") != connection_id])
    return list_connections(store)
