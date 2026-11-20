# Submodules and installing modules from a .zip: the parent counts as a requirement, healthy zips install and update,
# broken or tricky ones are refused before anything is written, included modules cannot be replaced or removed.
import io
import json
import zipfile
from pathlib import Path

import pytest

from studio.application import modules as mods
from studio.application.use_cases import StudioError
from studio.domain import modules as rules
from studio.infrastructure.module_store import JsonModuleStore
from studio.presentation.wiring import PROGRAM_DIR

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "modules" / "demo_mqtt"


def make_zip(files: dict) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as package:
        for name, content in files.items():
            package.writestr(name, content)
    return buffer.getvalue()


def demo_files(folder="demo_mqtt/", **manifest_changes) -> dict:
    manifest = {**json.loads((FIXTURE / "module.json").read_text(encoding="utf-8")), **manifest_changes}
    return {f"{folder}module.json": json.dumps(manifest), f"{folder}translate.py": (FIXTURE / "translate.py").read_text()}


@pytest.fixture
def store(tmp_path):
    return JsonModuleStore(PROGRAM_DIR, tmp_path)


def test_a_submodule_needs_its_parent():
    parent = {"id": "conexiones", "name": "c", "version": "1", "license": "MIT"}
    child = {"id": "x", "name": "x", "version": "1", "license": "MIT", "parent": "conexiones"}
    order, issues = rules.active_order({"conexiones": parent, "x": child}, {"x"})
    assert order == [] and issues[0]["requires"] == "conexiones"
    assert rules.required_by({"conexiones": parent, "x": child}, {"x"}, "conexiones") == ["x"]


def test_inspect_shows_what_it_adds_and_writes_nothing(store, tmp_path):
    summary = mods.inspect_package(store, make_zip(demo_files()))
    assert summary["parent"] == "conexiones" and summary["adds"] == ["connector:demo_mqtt"]
    assert summary["replaces"] is None and not (tmp_path / "modules").exists()


def test_install_turns_it_on_and_a_new_version_replaces_the_old(store, tmp_path):
    for folder in ("demo_mqtt/", "", "demo_mqtt\\"):  # a zipped folder, the files at the root, or \ in names
        mods.install_package(store, make_zip(demo_files(folder)))
    listed = {m["id"]: m for m in mods.list_modules(store)["modules"]}
    assert listed["demo_mqtt"]["origin"] == "installed" and listed["demo_mqtt"]["active"]
    assert "_dir" not in listed["demo_mqtt"]
    newer = make_zip(demo_files(version="1.1.0"))
    assert mods.inspect_package(store, newer)["replaces"] == "1.0.0"
    mods.install_package(store, newer)
    assert json.loads((tmp_path / "modules" / "demo_mqtt" / "module.json").read_text())["version"] == "1.1.0"


@pytest.mark.parametrize("files, code", [
    ({"../evil/module.json": "{}"}, "E_EXT_UNSAFE_PATH"),
    ({"readme.txt": "hola"}, "E_EXT_NO_MANIFEST"),
    ({"a/module.json": "{}", "b/module.json": "{}"}, "E_EXT_MANY_MANIFESTS"),
    ({"module.json": "not json"}, "E_EXT_NO_MANIFEST"),
    ({"module.json": json.dumps({"id": "x"})}, "E_MODULE_MANIFEST"),
])
def test_tricky_or_broken_zips_are_refused(store, tmp_path, files, code):
    with pytest.raises(StudioError) as err:
        mods.install_package(store, make_zip(files))
    assert err.value.code == code and not (tmp_path / "modules").exists()


def test_not_a_zip_a_connector_without_translate_and_an_included_id_are_refused(store):
    cases = [(b"hello", "E_EXT_BAD_ZIP"),
             (make_zip({"module.json": demo_files("")["module.json"]}), "E_EXT_MISSING_FILE"),
             (make_zip(demo_files(id="conexiones")), "E_EXT_INCLUDED")]
    for data, code in cases:
        with pytest.raises(StudioError) as err:
            mods.install_package(store, data)
        assert err.value.code == code


def test_uninstall_only_installed_modules_and_never_a_parent_with_submodules(store, tmp_path):
    with pytest.raises(StudioError) as err:
        mods.uninstall_module(store, "conexiones")
    assert err.value.code == "E_EXT_INCLUDED"
    mods.install_package(store, make_zip(demo_files()))
    child = demo_files("", id="demo_child", parent="demo_mqtt")
    child["module.json"] = json.dumps({**json.loads(child["module.json"]), "adds": {}})
    mods.install_package(store, make_zip(child))
    with pytest.raises(StudioError) as err:
        mods.uninstall_module(store, "demo_mqtt")
    assert err.value.code == "E_MODULE_REQUIRED_BY"
    mods.uninstall_module(store, "demo_child")
    result = mods.uninstall_module(store, "demo_mqtt")
    assert "demo_mqtt" not in {m["id"] for m in result["modules"]}
    assert not (tmp_path / "modules" / "demo_mqtt").exists()
