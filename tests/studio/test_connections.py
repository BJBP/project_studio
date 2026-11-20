# External connections: connectors found in the data folder, option checks, one commander per device, and saving
# through the use cases. Uses a neutral test connector (tests/studio/fixtures/connectors/demo_mqtt).
import json
import shutil
from pathlib import Path

import pytest

from studio.application import connections as conns
from studio.application.use_cases import StudioError
from studio.domain.connections import check_all
from studio.infrastructure.connection_store import JsonConnectionStore

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "connectors"
LAMP = {"entity_id": "switch.lamp", "remote_id": "lamp-1", "direction": "both"}


def conn(cid="panel", **extra):
    return {"id": cid, "name": "Panel", "type": "demo_mqtt", "options": {"port": 1885}, "devices": [LAMP], **extra}


@pytest.fixture
def store(tmp_path):
    shutil.copytree(FIXTURE, tmp_path / "connectors")  # installed in the data folder, as a private one would be
    return JsonConnectionStore(ROOT, tmp_path)


def test_connectors_installed_in_the_data_folder_are_found_without_their_path(store):
    assert "demo_mqtt" in store.connectors()
    listed = conns.list_connections(store)["connectors"]
    assert [c["type"] for c in listed] == ["demo_mqtt"] and "_dir" not in listed[0]


def test_save_lists_with_defaults_and_rereads(store):
    result = conns.save_connection(store, conn())
    assert result["issues"] == []
    assert result["connections"][0]["options"] == {"host": "127.0.0.1", "port": 1885}
    assert json.loads(store.file.read_text(encoding="utf-8"))["connections"][0]["id"] == "panel"


def test_bad_port_unknown_type_and_bad_remote_id_are_refused(store):
    for bad, code in ((conn(options={"port": 70000}), "E_CONN_OPTION"), (conn(type="nothing"), "E_CONN_TYPE"),
                      (conn(devices=[{**LAMP, "remote_id": "a/b"}]), "E_CONN_DEVICE")):
        with pytest.raises(StudioError) as err:
            conns.save_connection(store, bad)
        assert err.value.code == code


def test_only_one_connection_may_give_orders_to_a_device(store):
    connectors = store.connectors()
    assert [i["code"] for i in check_all([conn("a"), conn("b")], connectors)] == ["E_CONN_COMMANDS"]
    assert check_all([conn("a"), conn("b", devices=[{**LAMP, "direction": "send"}])], connectors) == []


def test_delete(store):
    conns.save_connection(store, conn())
    assert conns.delete_connection(store, "panel")["connections"] == []
