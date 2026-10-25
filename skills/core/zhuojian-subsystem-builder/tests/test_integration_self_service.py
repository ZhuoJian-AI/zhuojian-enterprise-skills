"""Participant discovery and bounded event recovery use only the Runtime API."""
import copy
import hashlib
from io import BytesIO
import json
from unittest import mock

import pytest

from scripts import integration_plan as cli


PLAN = "33333333-3333-4333-8333-333333333333"
OTHER = "44444444-4444-4444-8444-444444444444"
EVENT = "55555555-5555-4555-8555-555555555555"
VERSION = "a" * 64
FEATURE = {"supported": True, "version": 1, "contractProjectionRevision": 2,
           "recoveryScope": "original-plan-event-window", "requiresAdministratorSession": False}


def plan(identifier=PLAN):
    return {"id": identifier, "version": VERSION, "spec_digest": "b" * 64,
            "authorization_status": "approved", "edges": []}


def payload():
    return {"version": VERSION, "request_id": "workflow-recover-01", "reason": "恢复原范围遗漏投递",
            "items": [{"edge_key": "submit", "event_id": "real-original-event"}]}


def receipt(value=None):
    value = value or payload()
    return {"plan_id": PLAN, "request_id": value["request_id"], "version": value["version"],
            "request_digest": cli.recovery_digest(value), "business_completed": False,
            "items": [{**row, "delivery_id": "saved-delivery-id", "status": "pending"} for row in value["items"]]}


def client(*responses):
    result = mock.Mock(spec=cli.PlatformClient)
    result.request.side_effect = responses
    return result


def absent():
    return cli.RequestRejected(404, "recovery_request_not_found")


def posts(platform):
    return [call for call in platform.request.call_args_list if call.args[0] == "POST"]


def test_capability_cached_and_untrusted_returned_endpoints_never_used():
    opener = mock.Mock()
    opener.open.return_value = BytesIO(json.dumps({"features": {
        "integrationPlans": {"supported": True, "version": 1},
        "integrationPlanSelfService": {**FEATURE, "discoveryEndpoint": "https://evil.invalid/"},
    }}).encode())
    platform = cli.PlatformClient("https://platform.test", "synthetic-secret", opener=opener)
    platform.require_self_service()
    platform.require_self_service()
    assert opener.open.call_count == 1
    assert opener.open.call_args.args[0].full_url == "https://platform.test/api/v1/ecs-publisher/platform-capabilities"


@pytest.mark.parametrize("change", [{"version": True}, {"contractProjectionRevision": True},
                                   {"recoveryScope": "all-history"}, {"requiresAdministratorSession": True}])
def test_no_discovery_or_recovery_guessed_for_old_or_incompatible_servers(change):
    opener = mock.Mock()
    opener.open.return_value = BytesIO(json.dumps({"features": {
        "integrationPlans": {"supported": True, "version": 1},
        "integrationPlanSelfService": {**FEATURE, **change},
    }}).encode())
    platform = cli.PlatformClient("https://platform.test", "synthetic-secret", opener=opener)
    with pytest.raises(cli.UnsupportedSelfService):
        cli.discover(platform)
    assert opener.open.call_count == 1


def test_paged_participant_discovery_preserves_incomplete_status_and_filters_output():
    first = {**plan(), "raw_credential": "never-print"}
    platform = client({"items": [first], "has_more": True, "next_cursor": PLAN},
                      {"items": [plan(OTHER)], "has_more": False, "next_cursor": None})
    result = cli.discover(platform, limit=1)
    assert result["inventory_complete"] is False
    assert "never-print" not in json.dumps(result)
    second = cli.discover(platform, limit=1, cursor=result["next_cursor"])
    assert second["inventory_complete"] is True
    assert "cursor=" + PLAN in platform.request.call_args.args[1]
    assert not posts(platform)


@pytest.mark.parametrize("value", [
    {"items": [], "has_more": True, "next_cursor": PLAN},
    {"items": [plan()], "has_more": True, "next_cursor": OTHER},
    {"items": [plan()], "has_more": False, "next_cursor": PLAN},
    {"items": [plan(), plan()], "has_more": False, "next_cursor": None},
])
def test_malformed_pages_never_report_complete(value):
    with pytest.raises(cli.IntegrationPlanError):
        cli.discover(client(value))


def test_recovery_candidates_have_no_business_payload_or_implicit_write():
    page = {"plan_id": PLAN, "version": VERSION, "readiness": {"ready": True, "gaps": []},
            "items": [{"event_record_id": EVENT, "event_id": "e1", "edge_key": "submit",
                       "status": "not_queued", "source_sequence": 101, "payload": "private-data"}],
            "has_more": False, "next_cursor": None}
    platform = client(page)
    result = cli.recovery_list(platform, PLAN, "submit")
    assert result["business_completed"] is False
    assert "private-data" not in json.dumps(result)
    assert not posts(platform)


def test_recovery_reads_existing_receipt_and_never_requeues():
    platform = client(receipt())
    result = cli.recover(platform, PLAN, payload(), business_intent_confirmed=True)
    assert result["status"] == "existing"
    assert result["business_completed"] is False
    assert not posts(platform)


def test_recovery_canonical_digest_matches_saas_for_chinese_reason():
    raw = json.dumps(payload(), sort_keys=True, separators=(",", ":"), default=str).encode()
    assert cli.recovery_digest(payload()) == hashlib.sha256(raw).hexdigest()


def test_same_request_with_changed_reason_does_not_borrow_old_receipt():
    changed = {**payload(), "reason": "不同范围"}
    platform = client(receipt())
    with pytest.raises(cli.IntegrationPlanError, match="different content"):
        cli.recover(platform, PLAN, changed, business_intent_confirmed=True)
    assert not posts(platform)


def test_new_request_requires_typed_absence_and_current_version_then_posts_once():
    platform = client(absent(), plan(), receipt())
    result = cli.recover(platform, PLAN, payload(), business_intent_confirmed=True)
    assert result["status"] == "queued"
    assert result["business_completed"] is False
    assert len(posts(platform)) == 1
    assert posts(platform)[0].args[2] == payload()


@pytest.mark.parametrize("failure", [cli.RequestRejected(404), cli.RequestRejected(403),
                                    cli.IntegrationPlanError("read failed")])
def test_read_failure_or_generic_404_never_authorizes_a_post(failure):
    platform = client(failure)
    with pytest.raises(cli.IntegrationPlanError):
        cli.recover(platform, PLAN, payload(), business_intent_confirmed=True)
    assert not posts(platform)


def test_unknown_recovery_only_gets_same_request_and_reconciles():
    platform = client(absent(), plan(), cli.RequestOutcomeUnknown("timeout"), receipt())
    result = cli.recover(platform, PLAN, payload(), business_intent_confirmed=True)
    assert result["status"] == "reconciled"
    assert len(posts(platform)) == 1
    first, last = platform.request.call_args_list[0], platform.request.call_args_list[-1]
    assert first.args == last.args


@pytest.mark.parametrize("last", [absent(), cli.IntegrationPlanError("read failed"),
                                  {**receipt(), "business_completed": True}])
def test_unknown_or_malformed_receipt_stays_unknown_without_retry(last):
    platform = client(absent(), plan(), cli.RequestOutcomeUnknown("timeout"), last)
    result = cli.recover(platform, PLAN, payload(), business_intent_confirmed=True)
    assert result["status"] == "unknown"
    assert result["request_id"] == payload()["request_id"]
    assert len(posts(platform)) == 1


def test_changed_plan_version_stops_before_post():
    platform = client(absent(), {**plan(), "version": "c" * 64})
    with pytest.raises(cli.IntegrationPlanError, match="version changed"):
        cli.recover(platform, PLAN, payload(), business_intent_confirmed=True)
    assert not posts(platform)


def test_recovery_rejects_missing_scope_confirmation_duplicate_items_and_unbounded_list():
    platform = client()
    with pytest.raises(cli.IntegrationPlanError, match="Confirm"):
        cli.recover(platform, PLAN, payload())
    for bad in ({**payload(), "items": []}, {**payload(), "items": payload()["items"] * 2},
                {**payload(), "request_id": "other/request"}, {**payload(), "items": [{}] * 101}):
        with pytest.raises(cli.IntegrationPlanError):
            cli.recover(platform, PLAN, bad, business_intent_confirmed=True)
    platform.request.assert_not_called()


def test_route_discovery_exposes_eligibility_but_does_not_adopt():
    row = {"route_id": EVENT, "source_application_id": PLAN, "target_application_id": OTHER,
           "source_module_key": "submission", "target_module_key": "records", "event_type": "example.submitted.v1",
           "is_active": True, "deleted": False, "managed": False, "adoptable": True, "blockers": [],
           "private_config": "never-print"}
    platform = client({"items": [row], "has_more": False, "next_cursor": None})
    result = cli.discover_routes(platform, PLAN, target_application_id=OTHER)
    platform.require_route_adoption.assert_called_once()
    assert result["items"][0]["adoptable"] is True
    assert "never-print" not in json.dumps(result)
    assert not posts(platform)


def test_contradictory_route_adoption_is_not_reported_as_eligible():
    row = {"route_id": EVENT, "source_application_id": PLAN, "target_application_id": OTHER,
           "is_active": False, "deleted": False, "managed": False, "adoptable": True, "blockers": []}
    platform = client({"items": [row], "has_more": False, "next_cursor": None})
    with pytest.raises(cli.IntegrationPlanError, match="Contradictory"):
        cli.discover_routes(platform, PLAN)


def test_adoption_route_is_part_of_proposal_identity_and_needs_capability():
    proposal = {"request_id": "adopt-real-route", "title": "Adopt owned route", "purpose": "Maintain one relation",
                "data_description": "Metadata", "ownership_description": "Target owns record",
                "edges": [{"key": "submit", "kind": "forward", "source_application_id": PLAN,
                           "source_module_key": "submission", "target_application_id": OTHER,
                           "target_module_key": "records", "event_type": "example.submitted.v1",
                           "adopt_route_id": EVENT}]}
    value = {**plan(), **proposal}
    assert cli.proposal_from_plan(value) == proposal
    platform = client([value])
    assert cli.propose(platform, proposal)["status"] == "existing"
    platform.require_route_adoption.assert_called_once()
    changed = copy.deepcopy(proposal)
    changed["edges"][0]["adopt_route_id"] = OTHER
    with pytest.raises(cli.IntegrationPlanError, match="different plan"):
        cli.propose(client([value]), changed)
