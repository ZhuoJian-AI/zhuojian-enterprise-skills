"""Prevent the role-default empty-table regression at every release entry."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.audit_permission_upgrade import audit
from scripts.manifest_semantics import (
    checkbox_permission_report,
    validate_checkbox_permissions,
    validate_permission_policy,
)
from scripts.publish_subsystem import require_publishable_checkbox_permissions

ROOT = Path(__file__).resolve().parents[1]


def manifest(scopes=None):
    policy = {"group": "management", "mode": "configurable", "supportedScopes": scopes or ["all"]}
    return {"contractRevision": "2.4", "modules": [{"moduleKey": "products", "actions": [{
        "actionKey": "products.query", "operation": "query", "name": "查看本企业全部商品",
        "description": "查看当前企业的全部商品进度，不改变商品资料。", "permissionPolicy": policy,
    }]}]}


@pytest.mark.parametrize("revision", ["2.4", "2.5"])
@pytest.mark.parametrize("scope", ["self", "department", "department_and_children", "custom_departments", "all"])
def test_single_business_capability_is_valid_for_both_revisions(revision, scope):
    current = manifest([scope])
    current["contractRevision"] = revision
    assert not validate_checkbox_permissions(current)


@pytest.mark.parametrize("revision", ["2.4", "2.5"])
def test_fixed_workspaces_is_explicit_and_cannot_be_whitelisted_as_unchanged_legacy(revision):
    baseline = manifest(["all"])
    current = copy.deepcopy(baseline)
    current["contractRevision"] = revision
    current["modules"][0]["actions"][0]["permissionPolicy"] = {"group": "management", "mode": "workspaces"}
    assert not validate_checkbox_permissions(current)
    assert audit(current, baseline)["runtimeVerificationRequired"] is True
    assert current["modules"][0]["actions"][0]["permissionPolicy"] != baseline["modules"][0]["actions"][0]["permissionPolicy"]


def test_wire_compatibility_does_not_remove_the_new_publish_gate():
    current = manifest(["self", "all"])
    action = current["modules"][0]["actions"][0]
    assert not validate_permission_policy(action["permissionPolicy"], action["operation"])
    assert validate_checkbox_permissions(current)
    with pytest.raises(SystemExit, match="勾选授权"):
        require_publishable_checkbox_permissions(current)


def test_reviewed_legacy_boundary_survives_copy_edit_but_never_expands_grants(capsys):
    baseline = manifest(["self", "department", "all"])
    snapshot = copy.deepcopy(baseline)
    current = copy.deepcopy(baseline)
    current["modules"][0]["actions"][0]["name"] = "查看商品进度"
    report = checkbox_permission_report(current, baseline)
    assert report["errors"] == []
    assert len(report["legacyUpgradeRequired"]) == 2
    assert report["grantsModified"] is False
    require_publishable_checkbox_permissions(current, baseline)
    assert "PERMISSION UPGRADE REQUIRED" in capsys.readouterr().out
    assert baseline == snapshot
    assert audit(current, baseline)["legacyUpgradeRequired"]


def test_business_scope_labels_are_display_only_for_exact_legacy_compatibility():
    baseline = manifest(["self", "all"])
    current = copy.deepcopy(baseline)
    current["modules"][0]["actions"][0]["permissionPolicy"]["scopeLabels"] = {
        "self": "查看自己创建的商品", "all": "查看本企业全部商品",
    }
    report = checkbox_permission_report(current, baseline)
    assert report["errors"] == []
    assert len(report["legacyUpgradeRequired"]) == 1
    assert report["grantsModified"] is False
    assert validate_checkbox_permissions(current), "Labels alone cannot whitelist a new multi-scope Action"


@pytest.mark.parametrize("labels", [
    {"self": "查看自己创建的商品"}, {"self": "", "all": "查看全部商品"},
    {"self": "   ", "all": "查看全部商品"}, {"self": "x" * 161, "all": "查看全部商品"},
    {"self": "查看自己创建的商品", "all": "查看全部商品", "department": "多余"},
])
def test_partial_ambiguous_or_unbounded_business_labels_are_rejected(labels):
    current = manifest(["self", "all"])
    current["modules"][0]["actions"][0]["permissionPolicy"]["scopeLabels"] = labels
    assert validate_checkbox_permissions(current, current)


def test_scope_labels_cannot_change_personal_or_public_modes():
    for mode, group in (("self", "personal"), ("public_read", "public_read")):
        assert validate_permission_policy({"mode": mode, "group": group, "scopeLabels": {}}, "query")


def test_verified_equivalent_labels_preserve_underlying_legacy_scopes():
    baseline = manifest(["self", "department"])
    current = copy.deepcopy(baseline)
    policy = current["modules"][0]["actions"][0]["permissionPolicy"]
    policy["scopeLabels"] = {"self": "在所属部门录入新商品", "department": "在所属部门录入新商品"}
    assert not validate_permission_policy(policy, "create")
    assert checkbox_permission_report(current, baseline)["errors"] == []
    assert policy["supportedScopes"] == ["self", "department"]


@pytest.mark.parametrize("change", ["module", "key", "operation", "scope"])
def test_legacy_baseline_cannot_whitelist_a_new_or_changed_boundary(change):
    baseline = manifest(["self", "all"])
    current = copy.deepcopy(baseline)
    action = current["modules"][0]["actions"][0]
    if change == "module":
        current["modules"][0]["moduleKey"] = "other"
    elif change == "key":
        action["actionKey"] = "products.new-query"
    elif change == "operation":
        action["operation"] = "export"
    else:
        action["permissionPolicy"]["supportedScopes"] = ["department", "all"]
    assert validate_checkbox_permissions(current, baseline)


def test_missing_policy_is_only_compatible_for_the_exact_legacy_action():
    current = manifest()
    del current["modules"][0]["actions"][0]["permissionPolicy"]
    assert validate_checkbox_permissions(current)
    assert checkbox_permission_report(current, current)["legacyUpgradeRequired"]


@pytest.mark.parametrize("field", ["applicationSlug", "enterprise"])
def test_a_baseline_from_another_application_or_enterprise_cannot_authorize_compatibility(field):
    baseline = manifest(["self", "all"])
    current = copy.deepcopy(baseline)
    current[field] = "different" if field == "applicationSlug" else {"key": "different", "name": "Different"}
    assert validate_checkbox_permissions(current, baseline)


@pytest.mark.parametrize("field,value", [
    ("name", ""), ("description", ""), ("name", "查询本人记录"),
    ("description", "按当前角色的数据范围查询商品。"),
])
def test_admin_labels_must_explain_business_instead_of_technical_configuration(field, value):
    current = manifest()
    current["modules"][0]["actions"][0][field] = value
    assert validate_checkbox_permissions(current)


def test_source_cli_has_no_unconditional_legacy_bypass(tmp_path):
    from test_validate_source import write_valid_project

    project = write_valid_project(tmp_path)
    manifest_path = project / "subsystem.json"
    current = json.loads(manifest_path.read_text(encoding="utf-8"))
    current["modules"][0]["actions"][0]["permissionPolicy"]["supportedScopes"] = ["self", "all"]
    manifest_path.write_text(json.dumps(current), encoding="utf-8")
    baseline = tmp_path / "deployed-manifest.json"
    baseline.write_text(json.dumps(current), encoding="utf-8")
    command = [sys.executable, str(ROOT / "scripts/validate_source.py"), "--path", str(project)]
    denied = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    assert denied.returncode == 1 and "业务边界" in denied.stdout
    allowed = subprocess.run(command + ["--permission-baseline", str(baseline)], capture_output=True, text=True, encoding="utf-8")
    assert allowed.returncode == 0, allowed.stdout + allowed.stderr
    assert "PERMISSION UPGRADE REQUIRED" in allowed.stdout


def test_scaffold_requires_a_business_decision_before_creating_any_files(tmp_path):
    output = tmp_path / "must-not-exist"
    command = [sys.executable, str(ROOT / "scripts/scaffold_subsystem.py"), "--output", str(output),
               "--company-slug", "example", "--company-name", "Example", "--application-slug", "products",
               "--application-name", "Products", "--module-key", "products", "--module-name", "商品",
               "--department", "ops:运营:owner"]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode != 0 and "--record-access" in result.stderr
    assert not output.exists()
    result = subprocess.run(command + ["--record-access", "personal-created"], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stdout + result.stderr
    current = json.loads((output / "subsystem.json").read_text(encoding="utf-8"))
    assert not validate_checkbox_permissions(current)
    assert all("自己创建的" in action["name"] for action in current["modules"][0]["actions"])
    assert all(action["permissionPolicy"]["supportedScopes"] == ["self"] for action in current["modules"][0]["actions"])
