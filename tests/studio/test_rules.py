# Domain rules on the real example data: compatibility, licenses, equipment and purchases.
from studio.domain.compatibility import check_connections
from studio.domain.equipment import fit
from studio.domain.licenses import license_level, license_rows
from studio.domain.purchases import shopping_list
from studio.domain.validation import validate_component, validate_project


def test_catalog_and_examples_are_valid(repo):
    catalog = repo.catalog()
    assert all(not validate_component(c) for c in catalog.values())
    for pid in repo.project_ids():
        assert validate_project(repo.load_project(pid), catalog) == []


def test_openhab_breaks_the_voice_connections(repo):
    project, catalog = repo.load_project("domotica-voz"), repo.catalog()
    assert check_connections(project, catalog) == []
    project["slots"]["hub"]["component"] = "openhab"
    issues = check_connections(project, catalog)
    assert {(i["slot"], i["protocol"]) for i in issues} == {("hub", "wyoming")}
    assert len(issues) == 2


def test_license_levels(repo):
    catalog = repo.catalog()
    assert license_level(license_rows(repo.load_project("domotica-voz"), catalog)) == "ok"
    assert license_level(license_rows(repo.load_project("industrial"), catalog)) == "warn"
    project = repo.load_project("domotica-voz")
    catalog["ollama"]["license"]["commercial"] = "no"
    assert license_level(license_rows(project, catalog)) == "error"


def test_mini_pc_without_gpu_gets_the_light_ai(repo):
    result = fit(repo.load_project("domotica-voz"), repo.catalog(), repo.equipment()["mini-pc"])
    assert result["ok"] is True
    assert {i["code"] for i in result["issues"]} == {"W_VARIANT_SWITCH"}
    llm = next(i for i in result["items"] if i["slot"] == "llm")
    assert llm["variant"].startswith("qwen3:1.7b")


def test_shopping_totals_by_currency_and_missing_prices(repo):
    models = [{"id": "a", "part": "esp32-s3", "brand": "X", "model": "M1", "status": "tested", "meets": True,
               "offers": [{"store": "S", "price": 10.0, "currency": "USD"}, {"store": "T", "price": 12, "currency": "USD"}]},
              {"id": "b", "part": "mic-i2s", "brand": "Y", "model": "M2", "meets": False, "offers": []}]
    result = shopping_list(repo.load_project("domotica-voz"), repo.catalog(), models, 3, {"esp32-s3"})
    assert result["totals"] == {"USD": 30.0}
    assert result["missing_prices"] == len(result["rows"]) - 1
    assert result["bought"] == 1
    assert [i["code"] for i in result["issues"]] == ["W_MODEL_SPEC"]
