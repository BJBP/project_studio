# Do the chosen pieces still understand each other? Each connection names a protocol both ends must speak.
# check_connections(project, catalog) -> issues; alternatives(slot, catalog) -> components that fit that slot.


def check_connections(project: dict, catalog: dict) -> list:
    issues = []
    for conn in project["connections"]:
        ends = (conn["from"], conn["to"])
        for end, peer in (ends, ends[::-1]):
            component = catalog.get(project["slots"][end]["component"])
            if component and conn["protocol"] not in component["protocols"]:
                peer_component = catalog.get(project["slots"][peer]["component"], {})
                issues.append({"code": "E_PROTOCOL_MISMATCH", "slot": end, "component": component["name"],
                               "protocol": conn["protocol"], "peer": peer_component.get("name", peer)})
    return issues


def broken_connections(project: dict, catalog: dict) -> set:
    """Indexes of the connections with a mismatch, for drawing them in red."""
    bad = set()
    for index, conn in enumerate(project["connections"]):
        for end in (conn["from"], conn["to"]):
            component = catalog.get(project["slots"][end]["component"])
            if component and conn["protocol"] not in component["protocols"]:
                bad.add(index)
    return bad


def alternatives(slot: str, catalog: dict) -> list:
    return sorted((c for c in catalog.values() if slot in c["slots"]), key=lambda c: c["name"])
