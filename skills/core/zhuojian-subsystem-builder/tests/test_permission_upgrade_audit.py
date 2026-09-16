import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_permission_upgrade import audit


def manifest(policy=None):
    action = {"actionKey": "records.query", "operation": "query"}
    if policy is not None:
        action["permissionPolicy"] = policy
    return {"contractRevision": "2.4", "modules": [{"moduleKey": "records", "actions": [action]}]}


def test_new_missing_policy_fails_but_existing_is_upgrade_list():
    old = manifest()
    snapshot = copy.deepcopy(old)
    assert audit(old)["errors"]
    report = audit(old, old)
    assert not report["errors"]
    assert len(report["legacyUpgradeRequired"]) == 1
    assert old == snapshot
    assert report["grantsModified"] is False


def test_new_invalid_public_write_rejected():
    new = manifest({"group": "public_read", "mode": "public_read"})
    new["modules"][0]["actions"][0]["operation"] = "update"
    assert audit(new)["errors"]


def test_scope_change_requires_manual_verification():
    old = manifest({"group": "personal", "mode": "self"})
    new = manifest({"group": "management", "mode": "configurable", "supportedScopes": ["all"]})
    report = audit(new, old)
    assert not report["errors"]
    assert "人工核对" in report["changes"][0]["status"]
    assert report["runtimeVerificationRequired"]


def test_moving_legacy_action_to_new_module_does_not_copy_grant():
    old = manifest()
    new = copy.deepcopy(old)
    new["modules"][0]["moduleKey"] = "new-module"
    report = audit(new, old)
    assert report["errors"]
    assert len(report["changes"]) == 2
