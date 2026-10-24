"""Runtime-owned configuration decisions, without network or real credentials."""
import copy
from contextlib import redirect_stdout
from io import BytesIO, StringIO
import json
import unittest
from unittest import mock

from scripts import integration_plan as cli


APP_A = "11111111-1111-4111-8111-111111111111"
APP_B = "22222222-2222-4222-8222-222222222222"
PLAN = "33333333-3333-4333-8333-333333333333"
RT_A = "44444444-4444-4444-8444-444444444444"
RT_B = "55555555-5555-4555-8555-555555555555"
DIGEST = "d" * 64


def proposal(**changes):
    return {
        "request_id": "synthetic-runtime-link", "title": "Reuse record processing",
        "purpose": "One authoritative record", "data_description": "Synthetic metadata",
        "ownership_description": "Target owns the record; source keeps a result reference",
        "authorization_mode": cli.RUNTIME_MODE,
        "edges": [{"key": "submit", "kind": "forward", "source_application_id": APP_A,
                   "source_module_key": "submission", "target_application_id": APP_B,
                   "target_module_key": "records", "event_type": "example.submitted.v1"}],
        **changes,
    }


def plan(**changes):
    return {
        **proposal(), "configuration_ttl_hours": 72,
        "id": PLAN, "version": "a" * 64, "spec_digest": "b" * 64,
        "authorization_status": "pending", "configuration_status": "not_configured",
        "configuration_lease_expired": False, "apply_expires_at": "2030-01-04T00:00:00Z",
        "authorization_digest": DIGEST, "authorization_authority": "runtime_app_owners",
        "requires_administrator_session": False, "current_runtime_id": RT_A,
        "requester_runtime_id": RT_A, "current_runtime_application_ids": [APP_A],
        "current_runtime_can_confirm": True, "readiness": {"ready": True, "gaps": []},
        "runtime_confirmations": [
            {"runtime_id": RT_A, "application_ids": [APP_A], "confirmed": False, "valid": False, "confirmed_at": None},
            {"runtime_id": RT_B, "application_ids": [APP_B], "confirmed": False, "valid": False, "confirmed_at": None},
        ], **changes,
    }


def confirmed(*, approved=False):
    result = plan(authorization_status="approved" if approved else "pending", version="c" * 64)
    result["runtime_confirmations"][0].update(confirmed=True, valid=True, confirmed_at="2030-01-01T00:00:00Z")
    if approved:
        result["runtime_confirmations"][1].update(confirmed=True, valid=True)
    return result


def client(*responses):
    result = mock.Mock(spec=cli.PlatformClient)
    result.request.side_effect = responses
    return result


def decide(platform, operation="confirm", **changes):
    return cli.runtime_decision(platform, PLAN, DIGEST, operation=operation,
                                business_intent_confirmed=True, **changes)


class RuntimeConfirmationTests(unittest.TestCase):
    def test_runtime_capability_is_distinct_and_origin_endpoint_is_never_executed(self):
        feature = {"supported": True, "version": 1, "authorizationMode": cli.RUNTIME_MODE,
                   "authority": "runtime-owned-app-configuration", "allParticipantRuntimesRequired": True,
                   "requiresAdministratorSession": False, "endpoint": "https://untrusted.invalid/"}
        opener = mock.Mock()
        opener.open.return_value = BytesIO(json.dumps({"features": {
            "integrationPlans": {"supported": True, "version": 1},
            "integrationPlanRuntimeAuthorization": feature,
        }}).encode())
        platform = cli.PlatformClient("https://platform.test", "synthetic-secret", opener=opener)
        platform.require_runtime_authorization()
        platform.require_runtime_authorization()
        self.assertEqual(opener.open.call_count, 1)
        self.assertEqual(opener.open.call_args.args[0].full_url, "https://platform.test/api/v1/ecs-publisher/platform-capabilities")

    def test_legacy_or_incomplete_capability_never_guesses_a_decision_request(self):
        good = {"supported": True, "version": 1, "authorizationMode": cli.RUNTIME_MODE,
                "authority": "runtime-owned-app-configuration", "allParticipantRuntimesRequired": True,
                "requiresAdministratorSession": False}
        cases = [None, {**good, "version": True}, {**good, "requiresAdministratorSession": True},
                 {**good, "allParticipantRuntimesRequired": False}, {**good, "authority": "administrator"}]
        for feature in cases:
            with self.subTest(feature=feature):
                opener = mock.Mock()
                opener.open.return_value = BytesIO(json.dumps({"features": {
                    "integrationPlans": {"supported": True, "version": 1},
                    "integrationPlanRuntimeAuthorization": feature,
                }}).encode())
                platform = cli.PlatformClient("https://platform.test", "synthetic-secret", opener=opener)
                with self.assertRaises(cli.UnsupportedRuntimeAuthorization):
                    decide(platform)
                self.assertEqual(opener.open.call_count, 1)

    def test_missing_local_guard_or_bad_digest_has_no_network(self):
        for guard, digest in [(False, DIGEST), ("yes", DIGEST), (True, "a" * 63)]:
            platform = client()
            with self.subTest(guard=guard, digest=digest), self.assertRaises(cli.IntegrationPlanError):
                cli.runtime_decision(platform, PLAN, digest, operation="confirm", business_intent_confirmed=guard)
            self.assertEqual(platform.mock_calls, [])

    def test_confirm_payload_contains_only_public_digest_and_partial_is_not_approved(self):
        platform = client(plan(), confirmed())
        result = decide(platform)
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["authorization_status"], "pending")
        self.assertEqual(platform.request.call_args_list[-1], mock.call("POST", cli.API_ROOT + "/" + PLAN + "/confirm", {"authorization_digest": DIGEST}))
        self.assertEqual(result["authorization_authority"], "runtime_app_owners")

    def test_last_confirmation_can_change_version_without_changing_authorization_digest(self):
        platform = client(plan(), confirmed(approved=True))
        self.assertEqual(decide(platform)["authorization_status"], "approved")

    def test_same_runtime_owns_both_endpoints_and_confirms_once(self):
        before = plan(current_runtime_application_ids=[APP_A, APP_B])
        before["runtime_confirmations"] = [{"runtime_id": RT_A, "application_ids": [APP_B, APP_A], "confirmed": False, "valid": False}]
        after = copy.deepcopy(before)
        after["runtime_confirmations"][0].update(confirmed=True, valid=True)
        after["authorization_status"] = "approved"
        platform = client(before, after)
        self.assertEqual(decide(platform)["status"], "confirmed")
        self.assertEqual(platform.request.call_count, 2)

    def test_repeat_own_valid_confirmation_never_posts(self):
        platform = client(confirmed())
        self.assertEqual(decide(platform)["status"], "already_confirmed")
        platform.request.assert_called_once_with("GET", cli.API_ROOT + "/" + PLAN)

    def test_wrong_digest_scope_or_legacy_plan_never_posts(self):
        cases = [plan(authorization_digest="e" * 64), plan(authorization_mode="administrator"),
                 plan(current_runtime_application_ids=[]), plan(current_runtime_application_ids=[{}]),
                 plan(current_runtime_application_ids=[APP_B]), plan(requires_administrator_session=True)]
        for value in cases:
            with self.subTest(value=value), self.assertRaises(cli.IntegrationPlanError):
                platform = client(value)
                decide(platform)
            self.assertEqual(platform.request.call_count, 1)

    def test_expired_or_ineligible_scope_never_posts(self):
        for value in [plan(configuration_lease_expired=True), plan(current_runtime_can_confirm=False)]:
            platform = client(value)
            self.assertEqual(decide(platform)["status"], "not_ready")
            self.assertEqual(platform.request.call_count, 1)

    def test_unknown_confirm_requires_this_runtime_valid_saved_confirmation(self):
        platform = client(plan(), cli.RequestOutcomeUnknown("unknown"), confirmed())
        self.assertEqual(decide(platform)["status"], "reconciled")
        self.assertEqual([call.args[0] for call in platform.request.call_args_list], ["GET", "POST", "GET"])

    def test_others_confirmed_or_global_approved_never_proves_own_confirmation(self):
        other = plan(authorization_status="approved")
        other["runtime_confirmations"][1].update(confirmed=True, valid=True)
        platform = client(plan(), cli.RequestOutcomeUnknown("unknown"), other)
        self.assertEqual(decide(platform)["status"], "unknown")
        self.assertEqual([call.args[0] for call in platform.request.call_args_list], ["GET", "POST", "GET"])

    def test_unknown_read_failure_remains_unknown_without_another_post(self):
        platform = client(plan(), cli.RequestOutcomeUnknown("unknown"), cli.IntegrationPlanError("read failed"))
        self.assertEqual(decide(platform)["status"], "unknown")
        self.assertEqual(platform.request.call_count, 3)

    def test_incomplete_post_response_is_read_back_before_claiming_confirmation(self):
        bad = confirmed()
        del bad["runtime_confirmations"]
        platform = client(plan(), bad, confirmed())
        self.assertEqual(decide(platform)["status"], "reconciled")
        self.assertEqual([call.args[0] for call in platform.request.call_args_list], ["GET", "POST", "GET"])

    def test_changed_digest_or_common_deadline_readback_never_succeeds(self):
        for changes in [{"authorization_digest": "f" * 64}, {"apply_expires_at": "2030-01-06T00:00:00Z"}]:
            platform = client(plan(), cli.RequestOutcomeUnknown("unknown"), confirmed() | changes)
            with self.subTest(changes=changes):
                self.assertEqual(decide(platform)["status"], "unknown")
                self.assertEqual(platform.request.call_count, 3)

    def test_known_permission_or_conflict_rejection_is_not_retried(self):
        for status in [403, 409]:
            platform = client(plan(), cli.RequestRejected(status, "runtime_authorization_changed"))
            with self.subTest(status=status), self.assertRaises(cli.RequestRejected):
                decide(platform)
            self.assertEqual(platform.request.call_count, 2)

    def test_revoke_and_reject_unknown_reconcile_only_same_plan_terminal_state(self):
        for operation, state in [("revoke", "revoked"), ("reject", "rejected")]:
            platform = client(plan(), cli.RequestOutcomeUnknown("unknown"), plan(authorization_status=state))
            with self.subTest(operation=operation):
                result = decide(platform, operation, reason="Changed business scope")
                self.assertEqual(result["status"], "reconciled")
                self.assertEqual(platform.request.call_args_list[1].args[2], {"authorization_digest": DIGEST, "reason": "Changed business scope"})
                self.assertEqual(platform.request.call_count, 3)

    def test_current_new_owner_can_revoke_stale_relation_without_signing_old_snapshot(self):
        new_owner = "66666666-6666-4666-8666-666666666666"
        before = confirmed(approved=True) | {"current_runtime_id": new_owner,
                                             "current_runtime_application_ids": [APP_B],
                                             "current_runtime_can_confirm": False}
        after = copy.deepcopy(before) | {"authorization_status": "revoked"}
        platform = client(before, cli.RequestOutcomeUnknown("unknown"), after)
        self.assertEqual(decide(platform, "revoke")["status"], "reconciled")
        self.assertEqual(platform.request.call_count, 3)
        platform = client(before)
        with self.assertRaises(cli.IntegrationPlanError):
            decide(platform)
        self.assertEqual(platform.request.call_count, 1)

    def test_requester_only_apply_and_saved_own_confirmation_are_required_locally(self):
        cases = [(confirmed(approved=True) | {"requester_runtime_id": RT_B}, "requester_required"),
                 (plan(authorization_status="approved"), "not_ready")]
        for value, status in cases:
            platform = client(value)
            with self.subTest(status=status):
                self.assertEqual(cli.apply(platform, PLAN)["status"], status)
                self.assertEqual(platform.request.call_count, 1)

    def test_optional_real_administrator_authority_does_not_require_machine_quorum(self):
        before = plan(authorization_status="approved", authorization_authority="enterprise_administrator",
                      current_runtime_can_confirm=False)
        platform = client(before)
        self.assertEqual(decide(platform)["status"], "already_authorized_by_administrator")
        self.assertEqual(platform.request.call_count, 1)
        platform = client(before, before | {"configuration_status": "configured"})
        self.assertEqual(cli.apply(platform, PLAN)["status"], "configured")
        self.assertEqual(platform.request.call_args.args[2], {"version": before["version"]})

    def test_ttl_normalization_preserves_input_and_legacy_comparison(self):
        value = proposal()
        original = copy.deepcopy(value)
        self.assertEqual(cli.validate_proposal(value)["configuration_ttl_hours"], 72)
        self.assertEqual(value, original)
        old = {k: v for k, v in value.items() if k != "authorization_mode"}
        self.assertEqual(cli.validate_proposal(old | {"authorization_mode": "administrator"}), old)
        for ttl in [True, 0, 169, "72", None]:
            with self.subTest(ttl=ttl), self.assertRaises(cli.IntegrationPlanError):
                cli.validate_proposal(value | {"configuration_ttl_hours": ttl})

    def test_existing_request_changed_ttl_is_not_silently_accepted(self):
        platform = client([plan(configuration_ttl_hours=168)])
        with self.assertRaises(cli.IntegrationPlanError):
            cli.propose(platform, proposal())
        self.assertEqual(platform.request.call_count, 1)

    def test_first_new_mode_proposal_uses_matching_canonical_ttl(self):
        platform = client([], plan())
        self.assertEqual(cli.propose(platform, proposal())["status"], "proposed")
        self.assertEqual(platform.request.call_args.args[2]["configuration_ttl_hours"], 72)

    def test_cli_requires_explicit_guard_before_reading_a_runtime_key(self):
        with mock.patch.object(cli.PlatformClient, "from_runtime") as load:
            with mock.patch("sys.stderr"):
                with self.assertRaises(SystemExit):
                    cli.main(["confirm", "--plan-id", PLAN, "--authorization-digest", DIGEST])
            load.assert_not_called()

    def test_real_cli_parser_routes_exact_confirm_without_sending_local_guard(self):
        platform = client(plan(), confirmed())
        output = StringIO()
        with mock.patch.object(cli.PlatformClient, "from_runtime", return_value=platform), redirect_stdout(output):
            code = cli.main(["confirm", "--plan-id", PLAN, "--authorization-digest", DIGEST,
                             "--confirm-business-intent"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "confirmed")
        self.assertEqual(platform.request.call_args.args[2], {"authorization_digest": DIGEST})

    def test_summary_exposes_business_scope_and_confirmation_not_credentials(self):
        value = confirmed() | {"credential": "synthetic-secret", "admin_session": "synthetic-secret"}
        result = cli.safe_plan_summary(value)
        self.assertEqual(result["authorization_digest"], DIGEST)
        self.assertEqual(result["business_scope"]["ownership_description"], value["ownership_description"])
        self.assertNotIn("synthetic-secret", json.dumps(result))
        self.assertFalse(result["end_to_end_verified"])

    def test_participant_cannot_post_verification_and_missing_peer_scope_is_refused(self):
        platform = client(confirmed(approved=True) | {"requester_runtime_id": RT_B})
        self.assertEqual(cli.verify(platform, PLAN, ["synthetic-delivery"])["status"], "requester_required")
        self.assertEqual(platform.request.call_count, 1)
        value = plan()
        value["runtime_confirmations"] = value["runtime_confirmations"][:1]
        with self.assertRaises(cli.IntegrationPlanError):
            decide(client(value))

    def test_two_independent_runtime_transports_confirm_then_requester_applies(self):
        capabilities = {"features": {
            "integrationPlans": {"supported": True, "version": 1},
            "integrationPlanRuntimeAuthorization": {
                "supported": True, "version": 1, "authorizationMode": cli.RUNTIME_MODE,
                "authority": "runtime-owned-app-configuration", "allParticipantRuntimesRequired": True,
                "requiresAdministratorSession": False,
            },
        }}
        peer_before = confirmed() | {"current_runtime_id": RT_B, "current_runtime_application_ids": [APP_B]}
        peer_after = confirmed(approved=True) | {"current_runtime_id": RT_B, "current_runtime_application_ids": [APP_B]}
        configured = confirmed(approved=True) | {"configuration_status": "configured"}
        first_opener, peer_opener = mock.Mock(), mock.Mock()
        first_opener.open.side_effect = [BytesIO(json.dumps(value).encode()) for value in
                                        [capabilities, plan(), confirmed(), confirmed(approved=True), configured]]
        peer_opener.open.side_effect = [BytesIO(json.dumps(value).encode()) for value in
                                       [capabilities, peer_before, peer_after]]
        first = cli.PlatformClient("https://platform.test", "synthetic-first-key", opener=first_opener)
        peer = cli.PlatformClient("https://platform.test", "synthetic-peer-key", opener=peer_opener)
        self.assertEqual(decide(first)["authorization_status"], "pending")
        self.assertEqual(decide(peer)["authorization_status"], "approved")
        self.assertEqual(cli.apply(first, PLAN)["status"], "configured")
        for opener, expected_key in [(first_opener, "synthetic-first-key"), (peer_opener, "synthetic-peer-key")]:
            for call in opener.open.call_args_list:
                request = call.args[0]
                self.assertEqual(request.get_header("Authorization"), "Bearer " + expected_key)
                if request.data:
                    self.assertNotIn("synthetic-", request.data.decode())
        self.assertFalse(any(call.args[0].full_url.endswith("/apply") for call in peer_opener.open.call_args_list))


if __name__ == "__main__":
    unittest.main()
