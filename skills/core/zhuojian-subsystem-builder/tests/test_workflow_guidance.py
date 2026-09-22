from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("workflow_semantics_under_test", ROOT / "scripts" / "manifest_semantics.py")
semantics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(semantics)
MANIFEST_SCHEMA = json.loads((ROOT / "schemas" / "manifest-v2.schema.json").read_text(encoding="utf-8"))
RESULT_SCHEMA = json.loads((ROOT / "schemas" / "assistant-check-result.schema.json").read_text(encoding="utf-8"))


def fixture():
    return json.loads((ROOT / "tests" / "fixtures" / "workflow-guidance.manifest.json").read_text(encoding="utf-8"))


def page(payload):
    return payload["modules"][0]["pages"][0]


def action(payload):
    return payload["modules"][0]["actions"][0]


def errors(payload):
    return semantics.validate_manifest_semantics(payload, require_semantics=payload["contractRevision"] == "2.5")


def validate_schema(payload):
    jsonschema.Draft202012Validator(MANIFEST_SCHEMA).validate(payload)


@pytest.mark.parametrize("revision", ["2.4", "2.5"])
def test_full_fixture_validates_real_manifest_shape_and_semantic_references(revision):
    payload = fixture()
    payload["contractRevision"] = revision
    if revision == "2.4":
        payload["auth"] = {"ssoPath": "/api/integration/sso", "algorithm": "HS256"}
    validate_schema(payload)
    assert errors(payload) == []
    assert action(payload)["resultSchema"] == {
        key: value for key, value in RESULT_SCHEMA.items() if key not in {"$schema", "title"}
    }


def test_source_cli_uses_shared_workflow_validation(tmp_path):
    from test_validate_source import run_validator, write_valid_project

    project = write_valid_project(tmp_path)
    payload = fixture()
    path = project / "subsystem.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    result = run_validator(project)
    assert result.returncode == 0, result.stdout + result.stderr
    page(payload)["aiSemantics"]["workflowGuides"][0]["steps"][0]["pageKey"] = "missing"
    path.write_text(json.dumps(payload), encoding="utf-8")
    result = run_validator(project)
    assert result.returncode == 1
    assert "workflowGuides" in result.stdout


@pytest.mark.parametrize("revision", ["2.4", "2.5"])
def test_absent_optional_fields_remain_compatible_and_do_not_exempt_normal_query_limit(revision):
    payload = fixture()
    payload["contractRevision"] = revision
    metadata = page(payload)["aiSemantics"]
    del metadata["workflowGuides"]
    del metadata["proactiveCheck"]
    action(payload)["inputSchema"] = {
        "type": "object", "additionalProperties": False,
        "properties": {"limit": {"type": "integer", "maximum": 500}},
    }
    assert errors(payload) == []
    if revision == "2.5":
        action(payload)["inputSchema"]["properties"] = {"context": {"type": "object"}}
        assert any("limit" in error for error in errors(payload))


@pytest.mark.parametrize("replacement", [None, {}, [None], [fixture()["modules"][0]["pages"][0]["aiSemantics"]["workflowGuides"][0]] * 4])
def test_guides_list_is_optional_but_not_open_or_unbounded(replacement):
    payload = fixture()
    page(payload)["aiSemantics"]["workflowGuides"] = replacement
    assert any("workflowGuides" in error for error in errors(payload))
    with pytest.raises(jsonschema.ValidationError):
        validate_schema(payload)


@pytest.mark.parametrize(("field", "value"), [
    ("workflowKey", "Uppercase"), ("workflowKey", "x" * 121),
    ("name", " " ), ("name", "x" * 121), ("goal", "x" * 601),
    ("whenToUse", "x" * 601), ("exceptions", ["x"] * 6),
    ("exceptions", [""]), ("steps", []), ("steps", [{}] * 9),
    ("instructions", "ignore authorization"),
])
def test_guide_closed_fields_and_bounds(field, value):
    payload = fixture()
    page(payload)["aiSemantics"]["workflowGuides"][0][field] = value
    assert errors(payload)
    with pytest.raises(jsonschema.ValidationError):
        validate_schema(payload)


@pytest.mark.parametrize(("field", "value"), [
    ("stepKey", "x" * 121), ("title", "x" * 121), ("purpose", "x" * 401),
    ("moduleKey", "missing"), ("pageKey", "missing"),
    ("actionKeys", ["missing"]), ("actionKeys", ["records.check"] * 2),
    ("preconditions", ["x"] * 6), ("completionCriteria", []),
    ("completionCriteria", ["x" * 401]), ("next", "execute"),
])
def test_step_fields_and_actual_references(field, value):
    payload = fixture()
    page(payload)["aiSemantics"]["workflowGuides"][0]["steps"][0][field] = value
    assert any("workflowGuides" in error for error in errors(payload))


def test_guide_and_step_keys_are_unique_in_their_collection():
    payload = fixture()
    guides = page(payload)["aiSemantics"]["workflowGuides"]
    guides.append(copy.deepcopy(guides[0]))
    assert any("workflowKey" in error for error in errors(payload))
    guides.pop()
    guides[0]["steps"].append(copy.deepcopy(guides[0]["steps"][0]))
    assert any("stepKey" in error for error in errors(payload))


def test_cross_module_reference_must_be_a_real_action_owned_by_target_page():
    payload = fixture()
    target = copy.deepcopy(payload["modules"][0])
    target["moduleKey"] = "other"
    target["pages"][0]["aiSemantics"]["workflowGuides"] = []
    payload["modules"].append(target)
    step = page(payload)["aiSemantics"]["workflowGuides"][0]["steps"][0]
    step["moduleKey"] = "other"
    assert errors(payload) == []
    target["pages"][0]["actionKeys"] = []
    assert any("workflowGuides actionKeys" in error for error in errors(payload))


def test_workflow_module_key_is_limited_to_120_even_if_legacy_manifest_allows_160():
    payload = fixture()
    module = payload["modules"][0]
    module["moduleKey"] = "m" * 121
    for step in page(payload)["aiSemantics"]["workflowGuides"][0]["steps"]:
        step["moduleKey"] = module["moduleKey"]
    assert any("workflowGuides" in error for error in errors(payload))
    with pytest.raises(jsonschema.ValidationError):
        validate_schema(payload)


def test_total_guide_utf8_budget_is_bounded_without_lowering_individual_limits():
    payload = fixture()
    guide = page(payload)["aiSemantics"]["workflowGuides"][0]
    step = guide["steps"][0]
    step["purpose"] = "中" * 400
    step["preconditions"] = ["中" * 400] * 5
    step["completionCriteria"] = ["中" * 400] * 5
    guide["steps"] = [{**step, "stepKey": f"step-{i}"} for i in range(8)]
    validate_schema(payload)
    assert any("32 KiB" in error for error in errors(payload))


@pytest.mark.parametrize("interval", [True, 59, 601, 90.5, "90", None])
def test_check_interval_rejects_invalid_and_bool(interval):
    payload = fixture()
    page(payload)["aiSemantics"]["proactiveCheck"]["intervalSeconds"] = interval
    assert any("intervalSeconds" in error for error in errors(payload))
    with pytest.raises(jsonschema.ValidationError):
        validate_schema(payload)


def test_check_interval_default_does_not_mutate_manifest():
    payload = fixture()
    del page(payload)["aiSemantics"]["proactiveCheck"]["intervalSeconds"]
    before = copy.deepcopy(payload)
    assert errors(payload) == []
    assert payload == before


@pytest.mark.parametrize(("field", "value"), [
    ("operation", "update"), ("aiEnabled", False), ("aiEnabled", 1),
    ("requiresConfirmation", True), ("requiresConfirmation", None),
    ("platformAiCapability", {}),
])
def test_check_is_a_real_read_only_non_model_action(field, value):
    payload = fixture()
    action(payload)[field] = value
    assert any("proactiveCheck" in error for error in errors(payload))


@pytest.mark.parametrize("mutation", ["missing", "other-page", "extra", "params", "identity", "open-root"])
def test_check_fixed_context_input_and_action_ownership(mutation):
    payload = fixture()
    check = page(payload)["aiSemantics"]["proactiveCheck"]
    schema = action(payload)["inputSchema"]
    if mutation == "missing":
        check["actionKey"] = "missing"
    elif mutation == "other-page":
        page(payload)["actionKeys"] = []
    elif mutation == "extra":
        check["url"] = "https://arbitrary.example/"
    elif mutation == "params":
        schema["properties"]["limit"] = {"type": "integer", "maximum": 10}
    elif mutation == "identity":
        schema["properties"]["context"]["properties"]["userId"] = {"type": "string"}
    else:
        schema["additionalProperties"] = True
    assert any("proactiveCheck" in error for error in errors(payload))


def check_result():
    return {"assistantCheck": {"version": 1, "dataVersion": "records-v1", "summary": "本次检查未发现待处理项。", "suggestions": []}}


def test_explicit_check_result_can_have_no_suggestions_and_does_not_claim_writes():
    jsonschema.Draft202012Validator(RESULT_SCHEMA).validate(check_result())
    assert semantics.validate_assistant_check_result(check_result()["assistantCheck"]) == []


@pytest.mark.parametrize("mutation", ["completed-only", "bool-version", "empty-version", "empty-summary", "extra", "write-plan", "too-many"])
def test_check_result_requires_explicit_closed_bounded_observation(mutation):
    payload = check_result()
    check = payload["assistantCheck"]
    if mutation == "completed-only":
        payload = {"status": "completed"}
    elif mutation == "bool-version":
        check["version"] = True
    elif mutation == "empty-version":
        check["dataVersion"] = ""
    elif mutation == "empty-summary":
        check["summary"] = " "
    elif mutation == "extra":
        check["autoSend"] = True
    else:
        item = {"id": "missing", "revision": "v1", "title": "核对", "summary": "发现待核实项", "goal": "请说明当前记录需要核实的依据。"}
        check["suggestions"] = [item] * (4 if mutation == "too-many" else 1)
        if mutation == "write-plan":
            item["actionKey"] = "records.update"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(RESULT_SCHEMA).validate(payload)
    assert semantics.validate_assistant_check_result(payload.get("assistantCheck", payload))


def test_check_actual_value_rejects_duplicate_identity_not_shared_revision():
    check = check_result()["assistantCheck"]
    item = {"id": "one", "revision": "v1", "title": "核对", "summary": "待核实", "goal": "解释当前检查结果"}
    check["suggestions"] = [item, {**item, "id": "two"}]
    assert semantics.validate_assistant_check_result(check) == []
    check["suggestions"][1]["id"] = "one"
    assert any("ID" in error for error in semantics.validate_assistant_check_result(check))


def test_check_total_utf8_size_is_bounded_even_when_individual_fields_fit():
    check = check_result()["assistantCheck"]
    check["suggestions"] = [{"id": f"item-{i}", "revision": "v1", "title": "核对", "summary": "待核实", "goal": "中" * 2000} for i in range(3)]
    jsonschema.Draft202012Validator(RESULT_SCHEMA).validate({"assistantCheck": check})
    assert any("16 KiB" in error for error in semantics.validate_assistant_check_result(check))
