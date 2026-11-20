# Purchases and delivery documents of a project. shopping(repo, id, units=None) -> shopping list;
# set_bought / choose_model / set_units change the saved state; export_docs(repo, id, render) -> {file: text}.
from studio.application.use_cases import StudioError, get_project
from studio.domain.licenses import license_alerts, license_rows
from studio.domain.purchases import shopping_list

MAX_UNITS = 999


def shopping(repo, project_id: str) -> dict:
    project, state = get_project(repo, project_id), repo.load_state(project_id)
    result = shopping_list(project, repo.catalog(), repo.models(), state["units"], set(state["bought"]),
                           state.get("chosen", {}))
    return {**result, "units": state["units"]}


def _update_state(repo, project_id: str, change) -> dict:
    get_project(repo, project_id)
    state = repo.load_state(project_id)
    change(state)
    repo.save_state(project_id, state)
    return shopping(repo, project_id)


def set_units(repo, project_id: str, units) -> dict:
    try:
        units = int(units)
    except (TypeError, ValueError):
        units = 0
    if not 1 <= units <= MAX_UNITS:
        raise StudioError("E_UNITS", max=MAX_UNITS)
    return _update_state(repo, project_id, lambda s: s.update(units=units))


def set_bought(repo, project_id: str, part: str, bought: bool) -> dict:
    def change(state):
        parts = set(state["bought"])
        parts.add(part) if bought else parts.discard(part)
        state["bought"] = sorted(parts)
    return _update_state(repo, project_id, change)


def choose_model(repo, project_id: str, part: str, model_id: str) -> dict:
    if not any(m["id"] == model_id and m["part"] == part for m in repo.models()):
        raise StudioError("E_UNKNOWN_MODEL", model=model_id)
    return _update_state(repo, project_id, lambda s: s.setdefault("chosen", {}).update({part: model_id}))


def export_docs(repo, project_id: str, render) -> dict:
    """render: infrastructure renderer with licenses_md, notices_md and shopping_csv."""
    project, catalog = get_project(repo, project_id), repo.catalog()
    rows = license_rows(project, catalog)
    return {"licencias.md": render.licenses_md(project, rows, license_alerts(rows)),
            "THIRD_PARTY_NOTICES.md": render.notices_md(project, rows),
            "compras.csv": render.shopping_csv(shopping(repo, project_id)),
            "inventree_partes.csv": render.inventree_csv(project, shopping(repo, project_id)),
            "odoo_productos.csv": render.odoo_csv(project, shopping(repo, project_id))}
