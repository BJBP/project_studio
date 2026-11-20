# Modules: manifest checks, dependency order, turning on and off (studio.domain.modules, studio.application.modules).
import pytest

from studio.application import modules as mods
from studio.application.use_cases import StudioError
from studio.domain import modules as rules
from studio.infrastructure.module_store import JsonModuleStore
from studio.presentation.wiring import PROGRAM_DIR


def manifest(mid, requires=()):
    return {"id": mid, "name": mid, "version": "1.0.0", "license": "MIT", "requires": list(requires), "adds": {}}


class MemoryStore:
    def __init__(self, manifests, enabled=None):
        self._manifests, self._enabled = {m["id"]: m for m in manifests}, enabled

    def manifests(self):
        return self._manifests

    def enabled(self):
        return None if self._enabled is None else set(self._enabled)

    def save_enabled(self, ids):
        self._enabled = set(ids)


def test_incomplete_manifest_is_reported():
    assert rules.check_manifest({"id": "x"})[0]["code"] == "E_MODULE_MANIFEST"
    bad = {**manifest("x"), "adds": {"blocks": [{"tab": "t"}], "sounds": []}}
    assert len(rules.check_manifest(bad)) == 2


def test_dependencies_come_first_and_missing_or_cyclic_ones_stay_off():
    found = {m["id"]: m for m in (manifest("tab"), manifest("block", ["tab"]), manifest("a", ["b"]), manifest("b", ["a"]))}
    order, issues = rules.active_order(found, {"tab", "block", "a", "b"})
    assert order == ["tab", "block"]
    assert {i["code"] for i in issues} == {"E_MODULE_CYCLE"}
    order, issues = rules.active_order(found, {"block"})
    assert order == [] and issues[0]["code"] == "E_MODULE_REQUIRES"


def test_turning_off_a_module_others_need_is_refused_and_on_needs_its_requirements():
    store = MemoryStore([manifest("tab"), manifest("block", ["tab"])])
    assert set(mods.list_modules(store)["active"]) == {"tab", "block"}
    with pytest.raises(StudioError) as err:
        mods.set_enabled(store, "tab", False)
    assert err.value.code == "E_MODULE_REQUIRED_BY"
    mods.set_enabled(store, "block", False)
    assert mods.set_enabled(store, "tab", False)["active"] == []
    with pytest.raises(StudioError) as err:
        mods.set_enabled(store, "block", True)
    assert err.value.code == "E_MODULE_REQUIRES"


def test_the_modules_the_program_brings_are_valid(tmp_path):
    result = mods.list_modules(JsonModuleStore(PROGRAM_DIR, tmp_path))
    assert result["issues"] == [] and len(result["active"]) == len(result["modules"]) >= 9
    assert not (tmp_path / "modules.json").exists()  # listing writes nothing to the user's folder
