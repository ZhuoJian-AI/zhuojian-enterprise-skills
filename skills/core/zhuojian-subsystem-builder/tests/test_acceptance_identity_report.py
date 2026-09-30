from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

from scripts import e2e_acceptance as acceptance


def manifest_with_action(action: dict) -> dict:
    return {"modules": [{
        "moduleKey": "people",
        "pages": [
            {"pageKey": "people.list", "actionKeys": [action["actionKey"]]},
            {"pageKey": "people.details", "actionKeys": [action["actionKey"]]},
            {"pageKey": "people.unrelated", "actionKeys": []},
        ],
        "actions": [action],
    }]}


def action_checks(results: list[dict]) -> set[str]:
    return {item["check"] for item in results if item["actionKey"] is not None}


@pytest.mark.parametrize("policy,operation,expected", [
    (None, "create", set()),
    ({"mode": "public_read"}, "query", set()),
    ({"mode": "configurable", "supportedScopes": ["department", "all"]}, "update", set()),
    ({"mode": "self"}, "query", {"personal_record_identity"}),
    ({"mode": "self"}, "export", {"personal_record_identity"}),
    ({"mode": "self"}, "create", {"personal_record_identity", "nameless_employee_form"}),
    ({"mode": "self"}, "update", {"personal_record_identity", "nameless_employee_form"}),
    ({"mode": "self"}, "delete", {"personal_record_identity", "nameless_employee_form"}),
    ({"mode": "self"}, "approve", {"personal_record_identity", "nameless_employee_form"}),
    ({"mode": "configurable", "supportedScopes": ["self", "all"]}, "create",
     {"personal_record_identity", "nameless_employee_form"}),
])
def test_only_declared_self_actions_add_personal_checks(policy, operation, expected):
    action = {"actionKey": "people.work", "operation": operation}
    if policy is not None:
        action["permissionPolicy"] = policy
    manifest = manifest_with_action(action)
    original = deepcopy(manifest)
    results = acceptance.pending_identity_results(manifest)

    assert manifest == original
    assert action_checks(results) == expected
    assert all(item["passed"] is None and item["failures"] for item in results)
    for item in results[2:]:
        assert item["moduleKey"] == "people"
        assert item["actionKey"] == "people.work"
        assert item["pageKeys"] == ["people.list", "people.details"]


@pytest.mark.parametrize("directory", [None, False, True])
def test_directory_pending_is_explicit_not_inferred_from_action_name(directory):
    action = {"actionKey": "people.member_save", "operation": "create"}
    if directory is not None:
        action["employeeDirectory"] = directory
    results = acceptance.pending_identity_results(manifest_with_action(action))
    assert action_checks(results) == ({"trusted_employee_selection"} if directory is True else set())


def test_undeclared_relations_and_legacy_routes_remain_unknown_not_passed():
    manifest = manifest_with_action({
        "actionKey": "people.member_save", "operation": "create",
        "inputSchema": {"properties": {"name": {"type": "string"}, "userId": {"type": "string"}}},
        "identity_acceptance_pass": True,
    })
    manifest["identity_results"] = [{"passed": True}]
    manifest["health"] = "healthy"
    results = acceptance.pending_identity_results(manifest)
    assert [item["check"] for item in results] == [
        "unified_http_authentication", "employee_identity_relationship_inventory",
    ]
    assert all(item["passed"] is None and item["actionKey"] is None for item in results)


def test_cross_module_page_links_and_simultaneous_declarations_are_kept_separate():
    first = manifest_with_action({
        "actionKey": "people.save", "operation": "update", "employeeDirectory": True,
        "permissionPolicy": {"mode": "self"},
    })
    first["modules"].append({
        "moduleKey": "other", "pages": [{"pageKey": "other.list", "actionKeys": ["other.save"]}],
        "actions": [{"actionKey": "other.save", "operation": "create", "employeeDirectory": True}],
    })
    results = acceptance.pending_identity_results(first)
    assert len(results) == 6
    assert results[-1]["moduleKey"] == "other"
    assert results[-1]["pageKeys"] == ["other.list"]
    assert all(item["pageKeys"] == ["people.list", "people.details"] for item in results[2:-1])


@pytest.mark.parametrize("revision", ["2.4", "2.5"])
@pytest.mark.parametrize("denied", [False, True])
def test_cli_technical_outcome_never_completes_real_identity_checks(monkeypatch, capsys, revision, denied):
    fixture = Path(__file__).parent / "fixtures" / "workflow-guidance.manifest.json"
    manifest = json.loads(fixture.read_text(encoding="utf-8"))
    manifest["contractRevision"] = revision
    if revision == "2.4":
        manifest["auth"] = {"ssoPath": "/api/integration/sso", "algorithm": "HS256"}
    values = {"ZHUOJIAN_ORGANIZATION_ID": "00000000-0000-0000-0000-000000000001"}
    if revision == "2.5":
        values.update({
            "ZHUOJIAN_MANIFEST_ACCESS_TOKEN": "zjmf_" + "a" * 40,
            "ZHUOJIAN_SSO_EXCHANGE_TOKEN": "zjss_" + "b" * 40,
            "ZHUOJIAN_ACTION_SIGNING_SECRET": "zjac_" + "c" * 40,
            "ZHUOJIAN_EVENT_SIGNING_SECRET": "zjev_" + "d" * 40,
        })
    else:
        values["ZHUOJIAN_INTEGRATION_SECRET"] = "test-only-legacy-" + "x" * 40
    calls = []

    def request(url, *, token, method="GET", body=None):
        calls.append((url, method, body))
        if url.endswith("/api/integration/manifest"):
            return 200, manifest
        if "/api/integration/sso?" in url:
            return (302 if revision == "2.4" else 422), {}
        assert url.endswith("/api/integration/actions/records.check")
        return (403, {"detail": "Not authorized"}) if denied else (200, {})

    monkeypatch.setattr(acceptance, "load_runtime_values", lambda *args: values)
    monkeypatch.setattr(acceptance, "json_request", request)
    arguments = ["e2e_acceptance.py", "--base-url", "https://example.invalid", "--module-key", "records",
                 "--page-key", "records.list", "--query-action", "records.check"]
    if denied:
        arguments.append("--expect-query-denied")
    monkeypatch.setattr(sys, "argv", arguments)

    assert acceptance.main() == 0
    output = capsys.readouterr().out
    report = json.loads(output.splitlines()[0])
    assert report["status"] == "pre_registration_only"
    assert report["subsystem_contract_pass"] is True
    assert report["realSso"] == "pending_admin_acceptance"
    assert report["identity_acceptance_pass"] is None
    assert report["identity_results"] == acceptance.pending_identity_results(manifest)
    assert all(item["passed"] is None for item in report["identity_results"])
    assert report["authorized_query_pass"] == ("not_run" if denied else "synthetic_only")
    assert len(calls) == 3
    assert calls[-1][2]["operation"] == "query"
    assert all(value not in output for key, value in values.items() if key != "ZHUOJIAN_ORGANIZATION_ID")
