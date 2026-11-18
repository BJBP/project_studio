# What the Studio can do: list projects, show one, swap or reset a piece, check it, tick the flow.
# Every function receives the repository (port) and returns plain dicts; failures raise StudioError(code).
import re
import unicodedata

from studio.domain.compatibility import alternatives, broken_connections, check_connections
from studio.domain.equipment import fit
from studio.domain.licenses import license_alerts, license_level, license_rows
from studio.domain.lifecycle import item_exists, stages_view
from studio.domain.validation import validate_project


class StudioError(Exception):
    def __init__(self, code: str, **params):
        super().__init__(code)
        self.code, self.params = code, params


def get_project(repo, project_id: str) -> dict:
    try:
        return repo.load_project(project_id)
    except KeyError:
        raise StudioError("E_PROJECT_NOT_FOUND", project=project_id) from None


def check_project(repo, project_id: str) -> list:
    project, catalog = get_project(repo, project_id), repo.catalog()
    issues = validate_project(project, catalog)
    return issues or check_connections(project, catalog) + license_alerts(license_rows(project, catalog))


def list_projects(repo) -> list:
    catalog, cards = repo.catalog(), []
    for project_id in repo.project_ids():
        project = repo.load_project(project_id)
        state = repo.load_state(project_id)
        flow = stages_view(project, catalog, set(state["done"]))
        cards.append({"id": project_id, "name": project["name"], "icon": project.get("icon", ""),
                      "status": project.get("status", "simulated"), "summary": project.get("summary", ""),
                      "pieces": len(project["slots"]), "licenses": license_level(license_rows(project, catalog)),
                      "problems": len(check_connections(project, catalog)),
                      "progress": [flow["done"], flow["total"]]})
    return cards


def project_view(repo, project_id: str) -> dict:
    project, catalog = get_project(repo, project_id), repo.catalog()
    state = repo.load_state(project_id)
    rows = license_rows(project, catalog)
    slots = {slot: {**choice, "info": catalog.get(choice["component"]),
                    "alternatives": [{"id": c["id"], "name": c["name"]} for c in alternatives(slot, catalog)]}
             for slot, choice in project["slots"].items()}
    return {"project": {**project, "slots": slots},
            "issues": check_connections(project, catalog),
            "broken": sorted(broken_connections(project, catalog)),
            "licenses": {"rows": rows, "alerts": license_alerts(rows), "level": license_level(rows)},
            "flow": stages_view(project, catalog, set(state["done"])),
            "equipment": [fit(project, catalog, repo.equipment()[e]) for e in project.get("equipment", [])
                          if e in repo.equipment()]}


def swap_component(repo, project_id: str, slot: str, component_id: str) -> dict:
    project, catalog = get_project(repo, project_id), repo.catalog()
    if slot not in project["slots"]:
        raise StudioError("E_UNKNOWN_SLOT", slot=slot)
    component = catalog.get(component_id)
    if not component or slot not in component["slots"]:
        raise StudioError("E_WRONG_SLOT", slot=slot, component=component_id)
    choice = project["slots"][slot]
    choice.setdefault("default", choice["component"])
    choice["component"] = component_id
    repo.save_project(project)
    return project_view(repo, project_id)


def reset_slot(repo, project_id: str, slot: str) -> dict:
    project = get_project(repo, project_id)
    choice = project["slots"].get(slot)
    if choice is None:
        raise StudioError("E_UNKNOWN_SLOT", slot=slot)
    choice["component"] = choice.get("default", choice["component"])
    repo.save_project(project)
    return project_view(repo, project_id)


def set_item_done(repo, project_id: str, item_id: str, done: bool) -> dict:
    project, catalog = get_project(repo, project_id), repo.catalog()
    if not item_exists(project, catalog, item_id):
        raise StudioError("E_UNKNOWN_ITEM", item=item_id)
    state = repo.load_state(project_id)
    items = set(state["done"])
    items.add(item_id) if done else items.discard(item_id)
    state["done"] = sorted(items)
    repo.save_state(project_id, state)
    return stages_view(project, catalog, items)


def create_project(repo, from_id: str, name: str) -> str:
    name = str(name or "").strip()
    if not name:
        raise StudioError("E_NAME_EMPTY")
    project = get_project(repo, from_id)
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    new_id = re.sub(r"[^a-z0-9]+", "-", plain).strip("-") or "proyecto"
    if new_id in repo.project_ids():
        raise StudioError("E_PROJECT_EXISTS", project=new_id)
    repo.save_project({**project, "id": new_id, "name": name, "from": from_id})
    return new_id
