# JSON API of the Studio page, framework-free so serve.py (standard library) can mount it.
# route(repo, method, path, body) -> (status, payload). Paths start with /api/studio/.
import base64
from urllib.parse import urlparse

from studio.application import connections as conns
from studio.application import modules as mods
from studio.application import shopping as shop
from studio.application import use_cases as uc
from studio.infrastructure.render import DocRenderer
from studio.presentation.messages import describe, t
from studio.presentation.wiring import build_connections, build_modules

PREFIX = "/api/studio/"
MAX_ZIP_BASE64 = 3 * 1024 * 1024  # a 2 MB zip in base64, with margin


def _with_messages(view: dict) -> dict:
    view["issues"] = [describe(i) for i in view["issues"]]
    view["licenses"]["alerts"] = [describe(a) for a in view["licenses"]["alerts"]]
    for equipment in view["equipment"]:
        equipment["issues"] = [describe(i) for i in equipment["issues"]]
    return view


def _shopping(result: dict) -> dict:
    return {**result, "issues": [describe(i) for i in result["issues"]]}


def _modules(result: dict) -> dict:
    return {**result, "issues": [describe(i) for i in result["issues"]]}


def _connections(repo, method: str, rest: list, body: dict):
    store = build_connections(repo)
    if method == "GET" and not rest:
        result = conns.list_connections(store)
    elif method == "POST" and not rest:
        result = conns.save_connection(store, body)
    elif method == "POST" and len(rest) == 2 and rest[1] == "delete":
        result = conns.delete_connection(store, rest[0])
    else:
        raise KeyError("/".join(["connections", *rest]))
    return {**result, "issues": [describe(i) for i in result["issues"]]}


def _zip_bytes(body: dict) -> bytes:
    """The .zip the page sends as base64 ({"zip": "..."})."""
    text = str(body.get("zip", ""))
    if len(text) > MAX_ZIP_BASE64:
        raise uc.StudioError("E_EXT_TOO_BIG", limit=2)
    try:
        return base64.b64decode(text, validate=True)
    except ValueError:
        raise uc.StudioError("E_EXT_BAD_ZIP") from None


def _routes(repo, method: str, parts: list, body: dict):
    """Returns the payload for one request; raises uc.StudioError or KeyError (unknown route)."""
    if parts[:1] == ["modules"]:
        store = build_modules(repo)
        if method == "GET" and len(parts) == 1:
            return _modules(mods.list_modules(store))
        if method == "POST" and parts[1:] == ["inspect"]:
            return mods.inspect_package(store, _zip_bytes(body))
        if method == "POST" and parts[1:] == ["install"]:
            return _modules(mods.install_package(store, _zip_bytes(body)))
        if method == "POST" and len(parts) == 3 and parts[2] == "uninstall":
            return _modules(mods.uninstall_module(store, parts[1]))
        if method == "POST" and len(parts) == 2:
            return _modules(mods.set_enabled(store, parts[1], bool(body.get("enabled"))))
        raise KeyError("/".join(parts))
    if parts[:1] == ["connections"]:
        return _connections(repo, method, parts[1:], body)
    if method == "GET" and parts == ["projects"]:
        return uc.list_projects(repo)
    if method == "POST" and parts == ["projects"]:
        return {"id": uc.create_project(repo, body.get("from", ""), body.get("name", ""))}
    if len(parts) < 2 or parts[0] != "projects":
        raise KeyError("/".join(parts))
    pid, rest = parts[1], parts[2:]
    table = {
        ("GET", ()): lambda: _with_messages(uc.project_view(repo, pid)),
        ("GET", ("check",)): lambda: [describe(i) for i in uc.check_project(repo, pid)],
        ("POST", ("swap",)): lambda: _with_messages(uc.swap_component(repo, pid, body.get("slot"), body.get("component"))),
        ("POST", ("reset",)): lambda: _with_messages(uc.reset_slot(repo, pid, body.get("slot"))),
        ("POST", ("names",)): lambda: uc.set_output_name(repo, pid, body.get("device"), body.get("key"), body.get("name", "")),
        ("POST", ("flow",)): lambda: uc.set_item_done(repo, pid, body.get("item"), bool(body.get("done"))),
        ("GET", ("shopping",)): lambda: _shopping(shop.shopping(repo, pid)),
        ("POST", ("shopping", "units")): lambda: _shopping(shop.set_units(repo, pid, body.get("units"))),
        ("POST", ("shopping", "bought")): lambda: _shopping(shop.set_bought(repo, pid, body.get("part"), bool(body.get("bought")))),
        ("POST", ("shopping", "model")): lambda: _shopping(shop.choose_model(repo, pid, body.get("part"), body.get("model"))),
        ("GET", ("docs",)): lambda: shop.export_docs(repo, pid, DocRenderer(t)),
    }
    return table[(method, tuple(rest))]()


def route(repo, method: str, path: str, body: dict | None = None) -> tuple[int, object]:
    url = urlparse(path)
    parts = [p for p in url.path[len(PREFIX):].split("/") if p]
    try:
        return 200, _routes(repo, method, parts, body or {})
    except uc.StudioError as err:
        issue = {"code": err.code, **err.params}
        return (404 if err.code == "E_PROJECT_NOT_FOUND" else 400), describe(issue)
    except KeyError:
        return 404, describe({"code": "E_ROUTE", "path": url.path})
