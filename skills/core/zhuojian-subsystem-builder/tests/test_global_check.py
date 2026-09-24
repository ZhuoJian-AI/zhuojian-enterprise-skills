from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("global_check_semantics_under_test", ROOT / "scripts" / "manifest_semantics.py")
semantics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(semantics)
MANIFEST_SCHEMA = json.loads((ROOT / "schemas" / "manifest-v2.schema.json").read_text(encoding="utf-8"))
RESULT_SCHEMA = json.loads((ROOT / "schemas" / "assistant-check-result.schema.json").read_text(encoding="utf-8"))


def fixture():
    payload = json.loads((ROOT / "tests" / "fixtures" / "workflow-guidance.manifest.json").read_text(encoding="utf-8"))
    metadata = page(payload)["aiSemantics"]
    del metadata["proactiveCheck"]
    metadata["globalCheck"] = {"actionKey": "records.check", "intervalSeconds": 300}
    action(payload)["inputSchema"] = {
        "type": "object", "additionalProperties": False, "required": ["context"],
        "properties": {"context": {
            "type": "object", "additionalProperties": False, "properties": {},
        }},
    }
    return payload


def page(payload):
    return payload["modules"][0]["pages"][0]


def action(payload):
    return payload["modules"][0]["actions"][0]


def errors(payload):
    return semantics.validate_manifest_semantics(payload, require_semantics=payload["contractRevision"] == "2.5")


def validate_schema(payload):
    jsonschema.Draft202012Validator(MANIFEST_SCHEMA).validate(payload)


@pytest.mark.parametrize("revision", ["2.4", "2.5"])
def test_global_check_is_optional_compatible_addition(revision):
    payload = fixture()
    payload["contractRevision"] = revision
    if revision == "2.4":
        payload["auth"] = {"ssoPath": "/api/integration/sso", "algorithm": "HS256"}
    validate_schema(payload)
    assert errors(payload) == []
    assert action(payload)["resultSchema"] == {
        key: value for key, value in RESULT_SCHEMA.items() if key not in {"$schema", "title"}
    }


def test_global_check_source_cli_uses_semantic_validator(tmp_path):
    from test_validate_source import run_validator, write_valid_project

    project = write_valid_project(tmp_path)
    payload = fixture()
    path = project / "subsystem.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    result = run_validator(project)
    assert result.returncode == 0, result.stdout + result.stderr
    action(payload)["inputSchema"]["properties"]["context"]["properties"]["userId"] = {"type": "string"}
    path.write_text(json.dumps(payload), encoding="utf-8")
    result = run_validator(project)
    assert result.returncode == 1
    assert "globalCheck" in result.stdout


@pytest.mark.parametrize("interval", [True, 59, 3601, 300.5, "300", None])
def test_global_interval_rejects_invalid_values(interval):
    payload = fixture()
    page(payload)["aiSemantics"]["globalCheck"]["intervalSeconds"] = interval
    assert any("globalCheck intervalSeconds" in error for error in errors(payload))
    with pytest.raises(jsonschema.ValidationError):
        validate_schema(payload)


def test_global_interval_default_does_not_mutate_manifest():
    payload = fixture()
    del page(payload)["aiSemantics"]["globalCheck"]["intervalSeconds"]
    before = copy.deepcopy(payload)
    assert errors(payload) == []
    assert payload == before


@pytest.mark.parametrize(("field", "value"), [
    ("operation", "update"), ("aiEnabled", False), ("aiEnabled", 1),
    ("requiresConfirmation", True), ("requiresConfirmation", None),
    ("platformAiCapability", None),
])
def test_global_check_is_a_real_read_only_non_model_action(field, value):
    payload = fixture()
    action(payload)[field] = value
    assert any("globalCheck" in error for error in errors(payload))


def test_global_check_requires_explicit_permission_policy():
    payload = fixture()
    del action(payload)["permissionPolicy"]
    assert any("globalCheck 绑定 Action 必须声明 permissionPolicy" in error for error in errors(payload))


def test_legacy_action_without_global_check_keeps_optional_permission_policy():
    payload = fixture()
    del page(payload)["aiSemantics"]["globalCheck"]
    del action(payload)["permissionPolicy"]
    assert not any("permissionPolicy" in error for error in errors(payload))


@pytest.mark.parametrize("mutation", [
    "missing", "other-page", "extra-check-field", "extra-param", "browser-field",
    "open-context", "open-root", "missing-context", "root-conditional",
])
def test_global_check_only_accepts_fixed_empty_context(mutation):
    payload = fixture()
    check = page(payload)["aiSemantics"]["globalCheck"]
    schema = action(payload)["inputSchema"]
    if mutation == "missing":
        check["actionKey"] = "missing"
    elif mutation == "other-page":
        page(payload)["actionKeys"] = []
    elif mutation == "extra-check-field":
        check["autoSend"] = True
    elif mutation == "extra-param":
        schema["properties"]["limit"] = {"type": "integer"}
    elif mutation == "browser-field":
        schema["properties"]["context"]["properties"]["route"] = {"type": "string"}
    elif mutation == "open-context":
        schema["properties"]["context"]["additionalProperties"] = True
    elif mutation == "open-root":
        schema["additionalProperties"] = True
    elif mutation == "missing-context":
        schema["required"] = []
    else:
        schema["allOf"] = [{}]
    assert any("globalCheck" in error for error in errors(payload))


@pytest.mark.parametrize("mutation", ["no-check", "version-two", "unbounded-suggestions", "unbounded-goal", "open-result"])
def test_global_result_schema_must_declare_bounded_assistant_check_v1(mutation):
    payload = fixture()
    schema = action(payload)["resultSchema"]
    if mutation == "no-check":
        schema["properties"] = {}
    elif mutation == "version-two":
        schema["properties"]["assistantCheck"]["properties"]["version"]["const"] = 2
    elif mutation == "unbounded-suggestions":
        del schema["properties"]["assistantCheck"]["properties"]["suggestions"]["maxItems"]
    elif mutation == "unbounded-goal":
        del schema["properties"]["assistantCheck"]["properties"]["suggestions"]["items"]["properties"]["goal"]["maxLength"]
    else:
        schema["additionalProperties"] = True
    assert any("globalCheck resultSchema" in error for error in errors(payload))


def test_global_check_does_not_exempt_unrelated_query_from_limit():
    payload = fixture()
    second = copy.deepcopy(action(payload))
    second["actionKey"] = "records.other_query"
    second["name"] = "其他查询"
    second["description"] = "另一项与跨页面检查不同的合成查询。"
    payload["modules"][0]["actions"].append(second)
    page(payload)["actionKeys"].append(second["actionKey"])
    page(payload)["aiSemantics"]["interactionAnchors"][0]["actionKeys"].append(second["actionKey"])
    assert any("records.other_query 必须提供" in error and "limit" in error for error in errors(payload))


def test_same_global_action_cannot_be_registered_on_two_pages():
    payload = fixture()
    second = copy.deepcopy(page(payload))
    second["pageKey"] = "records.detail"
    second["routePattern"] = "/records/detail"
    payload["modules"][0]["pages"].append(second)
    assert any("globalCheck actionKey 在同一应用内只能声明一次" in error for error in errors(payload))


def test_actual_global_check_result_reuses_v1_closed_bounded_result():
    response = {"assistantCheck": {
        "version": 1, "dataVersion": "snapshot-17",
        "summary": "来源：授权的业务汇总；截至 2026-09-24T10:00:00+08:00；一项待核对，非实时状态。",
        "suggestions": [{
            "id": "review-17", "revision": "evidence-17", "title": "核对业务记录",
            "summary": "来源：授权的业务汇总；截至 2026-09-24T10:00:00+08:00。",
            "goal": "请查询当前获权记录的依据；未经我确认不要修改。",
        }],
    }}
    jsonschema.Draft202012Validator(RESULT_SCHEMA).validate(response)
    assert semantics.validate_assistant_check_result(response["assistantCheck"]) == []
