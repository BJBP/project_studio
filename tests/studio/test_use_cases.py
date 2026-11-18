# Use cases and the JSON API with a temporary data folder.
import pytest

from studio.application import use_cases as uc
from studio.presentation.api import route
from studio.presentation.cli import main


def test_swap_and_reset_are_saved(repo):
    view = uc.swap_component(repo, "domotica-voz", "hub", "openhab")
    assert view["issues"] and view["broken"] == [3, 4]
    assert repo.load_project("domotica-voz")["slots"]["hub"]["component"] == "openhab"
    assert uc.reset_slot(repo, "domotica-voz", "hub")["issues"] == []


def test_swap_rejects_a_piece_for_another_slot(repo):
    with pytest.raises(uc.StudioError) as err:
        uc.swap_component(repo, "domotica-voz", "hub", "piper")
    assert err.value.code == "E_WRONG_SLOT"


def test_flow_progress_and_new_project(repo):
    flow = uc.set_item_done(repo, "domotica-voz", "comprar.esp32-s3", True)
    assert flow["done"] == 1
    new_id = uc.create_project(repo, "domotica-voz", "Cliente Pérez")
    assert new_id == "cliente-perez" and new_id in repo.project_ids()
    assert repo.load_state(new_id)["done"] == []


def test_api_messages_and_errors(repo):
    status, view = route(repo, "POST", "/api/studio/projects/domotica-voz/swap", {"slot": "hub", "component": "openhab"})
    assert status == 200 and "wyoming" in view["issues"][0]["message"]
    status, issue = route(repo, "GET", "/api/studio/projects/nope")
    assert status == 404 and issue["code"] == "E_PROJECT_NOT_FOUND"
    status, docs = route(repo, "GET", "/api/studio/projects/industrial/docs")
    assert "Grafana" in docs["licencias.md"] and docs["compras.csv"].startswith("Pieza")


def test_cli_check_fails_on_a_protocol_mismatch(repo, capsys):
    uc.swap_component(repo, "domotica-voz", "hub", "openhab")
    assert main(["check", str(repo.data_dir), "domotica-voz"]) == 1
    assert "E_PROTOCOL_MISMATCH" in capsys.readouterr().out
