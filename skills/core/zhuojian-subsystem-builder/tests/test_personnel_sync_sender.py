import importlib.util
from pathlib import Path
import sqlite3

import pytest

path = Path(__file__).resolve().parents[1] / "assets/admin-runtime/personnel-sync/directory_sync.py"
spec = importlib.util.spec_from_file_location("directory_sender",path)
sender = importlib.util.module_from_spec(spec); spec.loader.exec_module(sender)


def snapshot(active=True):
    return {"departments":[{"external_id":"d","name":"Dept"}],
        "employees":[{"external_id":"u","display_name":"Person","department_external_id":"d","is_active":active}]}


def test_lost_ack_restart_keeps_original_batch_id_and_retries(tmp_path):
    path = tmp_path/"state.sqlite"
    db = sender.connect(path)
    assert sender.enqueue(db,snapshot(),identity="org/runtime/source") == 1
    first = db.execute("SELECT request_id FROM outbox").fetchone()[0]
    def unavailable(_):raise sender.SyncError("Unavailable")
    with pytest.raises(sender.SyncError):sender.drain(db,unavailable)
    db.close()
    db = sender.connect(path)
    assert sender.enqueue(db,snapshot(),identity="org/runtime/source") == 0
    seen=[]
    assert sender.drain(db,lambda batch:seen.append(batch)) == 1
    assert seen[0]["request_id"] == first
    assert seen[0]["employees"][0]["source_version"] == 1


def test_departure_versions_and_omission_never_generate_departures(tmp_path):
    db=sender.connect(tmp_path/"state.sqlite")
    sender.enqueue(db,snapshot(),identity="source")
    sender.drain(db,lambda _:None)
    assert sender.enqueue(db,{"departments":[],"employees":[]},identity="source") == 0
    sender.enqueue(db,snapshot(False),identity="source")
    batches=[];sender.drain(db,lambda b:batches.append(b))
    assert batches[0]["departments"] == []
    assert batches[0]["employees"][0]["source_version"] == 2
    assert batches[0]["employees"][0]["is_active"] is False
    with pytest.raises(sender.SyncError):sender.enqueue(db,snapshot(),identity="different-enterprise")


@pytest.mark.parametrize("change",[{"is_active":"false"},{"role_ids":["admin"]},{"external_id":""}])
def test_source_contract_rejects_implicit_state_or_permissions(change):
    data=snapshot();data["employees"][0].update(change)
    with pytest.raises(sender.SyncError):sender.normalize(data)


def test_arbitrary_tree_order_and_cycle():
    data={"departments":[{"external_id":"b","name":"B","parent_external_id":"a"},
        {"external_id":"a","name":"A"}],"employees":[]}
    assert [r["external_id"] for r in sender.normalize(data)["departments"]]==["a","b"]
    data["departments"][1]["parent_external_id"]="b"
    with pytest.raises(sender.SyncError):sender.normalize(data)
