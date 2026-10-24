from __future__ import annotations

from io import BytesIO
from http.client import IncompleteRead
import copy
import json
import os
from urllib.error import HTTPError, URLError
from unittest import mock

import pytest

from scripts import integration_plan


def response(value):
    return BytesIO(json.dumps(value).encode())


def test_canonical_digest_is_order_independent_and_rejects_nan():
    assert integration_plan.canonical_json({"a": 1, "b": 2}) == integration_plan.canonical_json({"b": 2, "a": 1})
    with pytest.raises(integration_plan.IntegrationPlanError, match="finite JSON"):
        integration_plan.canonical_json({"value": float("nan")})


@pytest.mark.parametrize("origin", [
    "http://platform.test", "https://user:secret@platform.test",
    "https://platform.test/path", "https://platform.test?token=private",
    "https://platform.test#fragment", "https:///missing-host",
])
def test_transport_rejects_untrusted_origin(origin):
    with pytest.raises(integration_plan.IntegrationPlanError):
        integration_plan.PlatformClient(origin, "never-print-this")


def test_transport_uses_auth_header_not_url_and_returns_json():
    opener = mock.Mock()
    opener.open.return_value = response({"status": "pending"})
    client = integration_plan.PlatformClient("https://platform.test", "private-key", opener=opener)
    assert client.request("GET", "/api/v1/test") == {"status": "pending"}
    request = opener.open.call_args.args[0]
    assert "private-key" not in request.full_url
    assert request.get_header("Authorization") == "Bearer private-key"
    assert "private-key" not in repr(client)


def test_capability_discovery_is_authenticated_and_cached_for_one_client():
    opener = mock.Mock()
    opener.open.return_value = response({"features": {"integrationPlans": {"supported": True, "version": 1}}})
    client = integration_plan.PlatformClient("https://platform.test", "private-key", opener=opener)
    client.require_integration_plans()
    client.require_integration_plans()
    assert opener.open.call_count == 1
    request = opener.open.call_args.args[0]
    assert request.full_url.endswith("/api/v1/ecs-publisher/platform-capabilities")
    assert request.get_header("Authorization") == "Bearer private-key"


@pytest.mark.parametrize("value", [
    {}, {"features": {}}, {"features": {"integrationPlans": {"supported": False, "version": 1}}},
    {"features": {"integrationPlans": {"supported": True, "version": 0}}},
    {"features": {"integrationPlans": {"supported": True, "version": True}}},
])
def test_old_or_incomplete_capability_is_an_explicit_gap(value):
    opener = mock.Mock()
    opener.open.return_value = response(value)
    client = integration_plan.PlatformClient("https://platform.test", "private-key", opener=opener)
    with pytest.raises(integration_plan.UnsupportedPlatform, match="configuration remains unenabled"):
        client.require_integration_plans()
    assert opener.open.call_count == 1


def test_missing_old_capability_endpoint_is_an_explicit_gap_not_a_guessed_plan_request():
    opener = mock.Mock()
    opener.open.side_effect = HTTPError("https://platform.test", 404, "missing", {}, BytesIO(b"private-key"))
    client = integration_plan.PlatformClient("https://platform.test", "private-key", opener=opener)
    with pytest.raises(integration_plan.UnsupportedPlatform):
        client.require_integration_plans()
    assert opener.open.call_count == 1


@pytest.mark.parametrize("path", ["https://other.test/api/v1/x", "//other.test/api/v1/x", "/api/v1/\\other", "/api/v1/x#fragment"])
def test_transport_refuses_arbitrary_targets(path):
    opener = mock.Mock()
    client = integration_plan.PlatformClient("https://platform.test", "private-key", opener=opener)
    with pytest.raises(integration_plan.IntegrationPlanError):
        client.request("POST", path, {})
    opener.open.assert_not_called()


@pytest.mark.parametrize("code", [401, 403, 409, 422])
def test_rejection_is_sanitized_and_never_retried(code):
    opener = mock.Mock()
    opener.open.side_effect = HTTPError("https://platform.test", code, "private-key", {}, BytesIO(b"private-key"))
    client = integration_plan.PlatformClient("https://platform.test", "private-key", opener=opener)
    with pytest.raises(integration_plan.RequestRejected) as failure:
        client.request("POST", "/api/v1/test", {})
    assert failure.value.status == code
    assert "private-key" not in str(failure.value)
    assert opener.open.call_count == 1


def test_rejection_preserves_only_a_known_protocol_code():
    opener = mock.Mock()
    body = {"detail": {"code": "integration_not_ready", "message": "private-key", "auth_token": "private-key"}}
    opener.open.side_effect = HTTPError("https://platform.test", 409, "private-key", {}, response(body))
    client = integration_plan.PlatformClient("https://platform.test", "private-key", opener=opener)
    with pytest.raises(integration_plan.RequestRejected) as failure:
        client.request("POST", "/api/v1/test", {})
    assert failure.value.code == "integration_not_ready"
    assert "private-key" not in str(failure.value)
    assert "read current plan status" in str(failure.value)


@pytest.mark.parametrize("error", [URLError("private-key"), TimeoutError("private-key"), IncompleteRead(b"private-key"), HTTPError("https://platform.test", 503, "private-key", {}, None)])
def test_unknown_write_is_sanitized_and_never_retried(error):
    opener = mock.Mock()
    opener.open.side_effect = error
    client = integration_plan.PlatformClient("https://platform.test", "private-key", opener=opener)
    with pytest.raises(integration_plan.RequestOutcomeUnknown) as failure:
        client.request("POST", "/api/v1/test", {})
    assert "private-key" not in str(failure.value)
    assert opener.open.call_count == 1


def test_invalid_write_response_remains_unknown():
    opener = mock.Mock()
    opener.open.return_value = BytesIO(b"not-json-private-key")
    client = integration_plan.PlatformClient("https://platform.test", "private-key", opener=opener)
    with pytest.raises(integration_plan.RequestOutcomeUnknown):
        client.request("POST", "/api/v1/test", {})
    assert opener.open.call_count == 1


SOURCE_ID = "11111111-1111-4111-8111-111111111111"
TARGET_ID = "22222222-2222-4222-8222-222222222222"
PLAN_ID = "33333333-3333-4333-8333-333333333333"


def proposal():
    return {
        "request_id": "synthetic-request-1", "title": "Synthetic import link",
        "purpose": "Send approved input for processing", "data_description": "Synthetic test fields only",
        "ownership_description": "Destination owns the business record; source retains result reference",
        "edges": [{
            "key": "submit", "kind": "forward", "source_application_id": SOURCE_ID,
            "source_module_key": "submission", "event_type": "example.submitted.v1",
            "target_application_id": TARGET_ID, "target_module_key": "processing",
        }],
    }


def plan(**changes):
    return {
        **proposal(), "id": PLAN_ID, "version": "a" * 64, "spec_digest": "b" * 64,
        "authorization_status": "approved", "configuration_status": "not_configured",
        "configuration_lease_expired": False,
        "readiness": {"ready": True, "gaps": []},
        "transport_status": "not_sent", "business_status": "not_acknowledged",
        "approval_url": "https://admin.platform.test/integrations/" + PLAN_ID,
        "verification": {}, **changes,
    }


def two_edge_proposal():
    value = proposal()
    forward = value["edges"][0]
    forward["key"] = "submit"
    value["edges"].append({
        "key": "result", "kind": "result", "source_application_id": TARGET_ID,
        "source_module_key": "processing", "event_type": "example.processed.v1",
        "target_application_id": SOURCE_ID, "target_module_key": "submission",
    })
    return value


def two_edge_response(*, reverse=False):
    value = plan(**two_edge_proposal())
    value["edges"].sort(key=lambda edge: edge["key"], reverse=reverse)
    return value


def acknowledged_plan(**changes):
    return plan(
        configuration_status="configured", business_status="business_acknowledged",
        verification={
            "scope": "saved-target-receipts-only", "end_to_end_verified": False,
            "deliveries": [{
                "delivery_id": "actual-delivery-1", "edge_key": "submit",
                "transport_status": "transport_delivered", "business_status": "business_acknowledged",
                "processed": True,
                "receipt": {"id": "receipt-1", "status": "completed", "entityType": "example", "entityId": "record-1", "version": 1},
            }],
        }, **changes,
    )


def client_with(*results):
    client = mock.Mock(spec=integration_plan.PlatformClient)
    client.request.side_effect = results
    return client


def test_same_application_distinct_modules_are_supported():
    value = proposal()
    value["edges"][0]["target_application_id"] = SOURCE_ID
    assert integration_plan.validate_proposal(value) == value


def test_uuid_normalization_does_not_mutate_the_local_plan():
    value = proposal()
    value["edges"][0]["source_application_id"] = "ABCDEFAB-1111-4111-8111-111111111111"
    normalized = integration_plan.validate_proposal(value)
    assert normalized["edges"][0]["source_application_id"].startswith("abcdefab")
    assert value["edges"][0]["source_application_id"].startswith("ABCDEFAB")


@pytest.mark.parametrize("field,value", [("event_type", "*"), ("source_module_key", "all*"), ("target_module_key", "a b"), ("kind", "admin"), ("key", "../bad")])
def test_proposal_refuses_wildcards_unknown_kinds_and_arbitrary_targets(field, value):
    data = proposal()
    data["edges"][0][field] = value
    with pytest.raises(integration_plan.IntegrationPlanError):
        integration_plan.validate_proposal(data)


def test_proposal_refuses_extra_secret_or_role_fields():
    data = proposal()
    data["admin_token"] = "never-send"
    with pytest.raises(integration_plan.IntegrationPlanError):
        integration_plan.validate_proposal(data)
    data = proposal()
    data["edges"][0]["role"] = "admin"
    with pytest.raises(integration_plan.IntegrationPlanError):
        integration_plan.validate_proposal(data)


def test_proposal_refuses_duplicate_disconnected_and_third_app_edges():
    data = proposal()
    data["edges"].append(copy.deepcopy(data["edges"][0]))
    with pytest.raises(integration_plan.IntegrationPlanError, match="unique"):
        integration_plan.validate_proposal(data)
    data["edges"][1]["key"] = "second"
    data["edges"][1]["source_module_key"] = "elsewhere"
    data["edges"][1]["target_module_key"] = "unconnected"
    with pytest.raises(integration_plan.IntegrationPlanError, match="connected"):
        integration_plan.validate_proposal(data)
    data["edges"][1]["source_module_key"] = "submission"
    data["edges"][1]["target_application_id"] = PLAN_ID
    with pytest.raises(integration_plan.IntegrationPlanError, match="two applications"):
        integration_plan.validate_proposal(data)


def test_propose_reads_existing_request_and_never_reposts():
    client = client_with([plan()])
    result = integration_plan.propose(client, proposal())
    assert result["status"] == "existing"
    assert client.request.call_count == 1
    assert client.request.call_args.args[0] == "GET"


@pytest.mark.parametrize("reverse", [False, True])
def test_first_proposal_accepts_server_key_order_instead_of_claiming_specification_changed(reverse):
    value = two_edge_proposal()
    client = client_with([], two_edge_response(reverse=reverse))
    result = integration_plan.propose(client, value)
    assert result["status"] == "proposed"
    assert [call.args[0] for call in client.request.call_args_list] == ["GET", "POST"]
    assert [edge["key"] for edge in value["edges"]] == ["submit", "result"]


def test_existing_request_reconciles_the_same_keyed_graph_without_reposting():
    client = client_with([two_edge_response()])
    assert integration_plan.propose(client, two_edge_proposal())["status"] == "existing"
    client.request.assert_called_once()


def test_unknown_post_reconciles_reordered_server_graph_with_only_get():
    client = client_with([], integration_plan.RequestOutcomeUnknown("unknown"), [two_edge_response()])
    result = integration_plan.propose(client, two_edge_proposal())
    assert result["status"] == "reconciled"
    assert [call.args[0] for call in client.request.call_args_list] == ["GET", "POST", "GET"]


def test_edge_normalization_does_not_hide_changed_endpoint_or_event():
    value = two_edge_response()
    value["edges"][0]["event_type"] = "example.other.v1"
    client = client_with([value])
    with pytest.raises(integration_plan.IntegrationPlanError, match="different plan"):
        integration_plan.propose(client, two_edge_proposal())
    client.request.assert_called_once()


def test_request_id_cannot_be_reused_for_a_changed_plan():
    existing = plan(purpose="Different purpose")
    client = client_with([existing])
    with pytest.raises(integration_plan.IntegrationPlanError, match="different plan"):
        integration_plan.propose(client, proposal())
    assert client.request.call_count == 1


def test_unknown_proposal_only_reconciles_with_get():
    client = client_with([], integration_plan.RequestOutcomeUnknown("unknown"), [plan()])
    result = integration_plan.propose(client, proposal())
    assert result["status"] == "reconciled"
    assert [call.args[0] for call in client.request.call_args_list] == ["GET", "POST", "GET"]


def test_incomplete_proposal_response_is_reconciled_without_a_second_post():
    client = client_with([], {"accepted": True}, [plan()])
    result = integration_plan.propose(client, proposal())
    assert result["status"] == "reconciled"
    assert [call.args[0] for call in client.request.call_args_list] == ["GET", "POST", "GET"]


def test_unknown_proposal_not_found_remains_unknown_without_new_request_id():
    client = client_with([], integration_plan.RequestOutcomeUnknown("unknown"), [])
    result = integration_plan.propose(client, proposal())
    assert result["status"] == "unknown"
    assert result["request_id"] == proposal()["request_id"]
    assert [call.args[0] for call in client.request.call_args_list] == ["GET", "POST", "GET"]


@pytest.mark.parametrize("status", ["pending", "rejected", "revoked"])
def test_apply_never_posts_an_unapproved_plan(status):
    client = client_with(plan(authorization_status=status))
    result = integration_plan.apply(client, PLAN_ID)
    assert result["status"] == "not_approved"
    assert result["approval_url"].startswith("https://admin.")
    assert client.request.call_count == 1


@pytest.mark.parametrize("changes", [
    {"configuration_lease_expired": True},
    {"readiness": {"ready": False, "gaps": [{"code": "target_not_subscribed", "edge_key": "submit", "message": "Publish the target subscription and business handler"}]}},
])
def test_apply_not_ready_preserves_concrete_gaps_and_never_posts(changes):
    client = client_with(plan(**changes))
    result = integration_plan.apply(client, PLAN_ID)
    assert result["status"] == "not_ready"
    assert client.request.call_count == 1


def test_already_applied_plan_is_idempotent_after_configuration_lease_expires():
    client = client_with(plan(configuration_status="configured", configuration_lease_expired=True))
    result = integration_plan.apply(client, PLAN_ID)
    assert result["status"] == "already_configured"
    assert client.request.call_count == 1


def test_apply_uses_server_version_and_reconciles_unknown_without_retry():
    client = client_with(plan(), integration_plan.RequestOutcomeUnknown("unknown"), plan(configuration_status="configured", version="c" * 64))
    result = integration_plan.apply(client, PLAN_ID)
    assert result["status"] == "reconciled"
    assert client.request.call_args_list[1].args[2] == {"version": "a" * 64}
    assert [call.args[0] for call in client.request.call_args_list] == ["GET", "POST", "GET"]


def test_apply_rejects_changed_expected_version_and_specification():
    client = client_with(plan())
    with pytest.raises(integration_plan.IntegrationPlanError, match="version changed"):
        integration_plan.apply(client, PLAN_ID, "c" * 64)
    assert client.request.call_count == 1
    client = client_with(plan(), plan(spec_digest="c" * 64, configuration_status="configured"))
    with pytest.raises(integration_plan.IntegrationPlanError, match="specification changed"):
        integration_plan.apply(client, PLAN_ID)


def test_verify_requires_real_saved_target_receipt_and_never_calls_it_end_to_end():
    client = client_with(plan(configuration_status="configured"), acknowledged_plan())
    result = integration_plan.verify(client, PLAN_ID, ["actual-delivery-1"])
    assert result["status"] == "business_acknowledged"
    assert result["end_to_end_verified"] is False
    assert result["remaining_business_checks"]
    assert result["target_receipts"][0]["receipt"]["entityId"] == "record-1"
    assert client.request.call_args_list[1].args[2] == {"version": "a" * 64, "delivery_ids": ["actual-delivery-1"]}


@pytest.mark.parametrize("field,value", [("processed", False), ("receipt", None), ("edge_key", "unrelated"), ("delivery_id", "other-delivery"), ("business_status", "not_acknowledged")])
def test_verify_refuses_transport_only_or_unrelated_receipts(field, value):
    after = acknowledged_plan()
    after["verification"]["deliveries"][0][field] = value
    client = client_with(plan(configuration_status="configured"), after)
    result = integration_plan.verify(client, PLAN_ID, ["actual-delivery-1"])
    assert result["status"] == "not_acknowledged"
    assert "target_receipts" not in result


@pytest.mark.parametrize("field,value", [("status", "accepted"), ("entityId", ""), ("version", 0), ("version", True), ("contentSha256", "bad")])
def test_verify_refuses_incomplete_business_reference(field, value):
    after = acknowledged_plan()
    after["verification"]["deliveries"][0]["receipt"][field] = value
    client = client_with(plan(configuration_status="configured"), after)
    assert integration_plan.verify(client, PLAN_ID, ["actual-delivery-1"])["status"] == "not_acknowledged"


def test_verify_refuses_duplicate_delivery_ids_without_any_network():
    client = client_with()
    with pytest.raises(integration_plan.IntegrationPlanError, match="distinct"):
        integration_plan.verify(client, PLAN_ID, ["actual-delivery-1", "actual-delivery-1"])
    client.request.assert_not_called()


def test_unknown_verification_only_gets_saved_receipts_without_reposting():
    client = client_with(plan(configuration_status="configured"), integration_plan.RequestOutcomeUnknown("unknown"), acknowledged_plan())
    result = integration_plan.verify(client, PLAN_ID, ["actual-delivery-1"])
    assert result["status"] == "business_acknowledged"
    assert result["reconciled"] is True
    assert [call.args[0] for call in client.request.call_args_list] == ["GET", "POST", "GET"]


def test_platform_claim_of_end_to_end_success_is_not_accepted():
    after = acknowledged_plan()
    after["verification"]["end_to_end_verified"] = True
    client = client_with(plan(configuration_status="configured"), after)
    assert integration_plan.verify(client, PLAN_ID, ["actual-delivery-1"])["status"] == "not_acknowledged"


def test_selected_target_acknowledgement_does_not_complete_other_plan_edges():
    after = acknowledged_plan()
    after["business_status"] = "not_acknowledged"
    client = client_with(plan(configuration_status="configured"), after)
    result = integration_plan.verify(client, PLAN_ID, ["actual-delivery-1"])
    assert result["status"] == "partially_acknowledged"
    assert result["end_to_end_verified"] is False


def test_catalog_projects_only_nonsecret_contract_metadata():
    value = {"schema_version": 1, "environment": "test", "token": "never-print", "applications": [{
        "id": SOURCE_ID, "slug": "example", "name": "Example", "runtime_id": TARGET_ID,
        "owned_by_requester": True, "auth_token": "never-print", "modules": [{
            "key": "submission", "name": "Submission", "publishes": ["example.submitted.v1"],
            "subscribes": [], "payload": "never-print",
        }],
    }]}
    assert "never-print" not in json.dumps(integration_plan.safe_catalog(value))


def test_summary_projects_only_metadata_and_avoids_tokenized_approval_url():
    result = integration_plan.safe_plan_summary(plan(auth_token="never-print", approval_url="https://admin.platform.test/approve?token=never-print"))
    assert "never-print" not in json.dumps(result)
    assert "approval_url" not in result


@pytest.mark.parametrize("section_key", ["tab", "section"])
def test_summary_keeps_the_real_normal_admin_approval_route(section_key):
    url = "https://admin.platform.test/enterprise-apps/" + SOURCE_ID + "?integration_plan=" + PLAN_ID + "&" + section_key + "=integration"
    result = integration_plan.safe_plan_summary(plan(approval_url=url))
    assert result["approval_url"] == url


def test_runtime_profile_rejects_bad_origin_before_opening_a_key(tmp_path):
    profile = tmp_path / "runtime.json"
    profile.write_text(json.dumps({"platform": {"baseUrl": "https://user:secret@other.test"}, "deployment": {"registrationCredentialRef": "/protected/key"}}))
    with mock.patch.object(integration_plan, "read_runtime_key") as read:
        with pytest.raises(integration_plan.IntegrationPlanError):
            integration_plan.PlatformClient.from_runtime(profile)
    read.assert_not_called()


@pytest.mark.skipif(os.name == "nt", reason="POSIX protected-file semantics")
def test_runtime_key_refuses_a_permissive_file_and_a_symlink(tmp_path):
    key = tmp_path / "protected-key"
    key.write_text("never-print")
    key.chmod(0o644)
    with pytest.raises(integration_plan.IntegrationPlanError) as failure:
        integration_plan.read_runtime_key(key)
    assert "never-print" not in str(failure.value)
    key.chmod(0o600)
    link = tmp_path / "link"
    link.symlink_to(key)
    with pytest.raises(integration_plan.IntegrationPlanError):
        integration_plan.read_runtime_key(link)
