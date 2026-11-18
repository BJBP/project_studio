# Checks the shape of catalog components and projects. Receives plain dicts; returns a list of issues
# {"code": "E_...", ...params}. An empty list means valid.
COMPONENT_KEYS = ("id", "name", "kind", "slots", "protocols")
PROJECT_KEYS = ("id", "name", "slots", "connections", "hardware", "stages")


def validate_component(component: dict) -> list:
    issues = [{"code": "E_FIELD_MISSING", "where": component.get("id", "?"), "field": key}
              for key in COMPONENT_KEYS if key not in component]
    if component.get("kind") == "software" and "license" not in component:
        issues.append({"code": "E_FIELD_MISSING", "where": component.get("id", "?"), "field": "license"})
    return issues


def validate_project(project: dict, catalog: dict) -> list:
    pid = project.get("id", "?")
    issues = [{"code": "E_FIELD_MISSING", "where": pid, "field": key} for key in PROJECT_KEYS if key not in project]
    if issues:
        return issues
    for slot, choice in project["slots"].items():
        component = catalog.get(choice.get("component"))
        if not component:
            issues.append({"code": "E_UNKNOWN_COMPONENT", "slot": slot, "component": choice.get("component")})
        elif slot not in component["slots"]:
            issues.append({"code": "E_WRONG_SLOT", "slot": slot, "component": component["id"]})
    for conn in project["connections"]:
        for end in (conn.get("from"), conn.get("to")):
            if end not in project["slots"]:
                issues.append({"code": "E_UNKNOWN_SLOT", "slot": end})
    for item in project["hardware"]:
        if item.get("part") not in catalog:
            issues.append({"code": "E_UNKNOWN_COMPONENT", "slot": "hardware", "component": item.get("part")})
    return issues
