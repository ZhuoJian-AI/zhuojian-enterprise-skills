import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from manifest_semantics import validate_manifest_semantics, validate_permission_policy


@pytest.mark.parametrize("policy,operation", [
    (None, "update"),
    ({"group": "public_read", "mode": "public_read"}, "query"),
    ({"group": "personal", "mode": "self"}, "create"),
    ({"group": "management", "mode": "configurable", "supportedScopes": ["department", "all"]}, "approve"),
])
def test_valid(policy, operation):
    assert not validate_permission_policy(policy, operation)


@pytest.mark.parametrize("policy,operation", [
    ({"group": "public_read", "mode": "public_read"}, "create"),
    ({"group": "public_read", "mode": "public_read"}, "export"),
    ({"group": "personal", "mode": "self", "supportedScopes": ["all"]}, "update"),
    ({"group": "management", "mode": "configurable"}, "query"),
    ({"group": "management", "mode": "configurable", "supportedScopes": ["all", "all"]}, "query"),
    ({"group": "management", "mode": "configurable", "supportedScopes": ["cross_tenant"]}, "query"),
    ({"group": "personal", "mode": []}, "query"),
    ({"group": "personal", "mode": "self", "allowAll": True}, "query"),
])
def test_invalid(policy, operation):
    assert validate_permission_policy(policy, operation)


def test_legacy_contract_checks_present_policy_without_requiring_extension():
    action = {"actionKey": "example.create", "operation": "create", "aiEnabled": False}
    manifest = {"modules": [{"moduleKey": "example", "actions": [action]}]}
    assert not validate_manifest_semantics(manifest, require_semantics=False)
    action["permissionPolicy"] = {"group": "public_read", "mode": "public_read"}
    assert validate_manifest_semantics(manifest, require_semantics=False)
