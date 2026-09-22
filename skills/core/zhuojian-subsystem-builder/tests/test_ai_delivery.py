import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_ai_delivery.py"
SPEC = importlib.util.spec_from_file_location("validate_ai_delivery", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def manifest():
    return {
        "applicationSlug": "sample-review",
        "contractRevision": "2.5",
        "modules": [{
            "moduleKey": "review",
            "pages": [{"pageKey": "items", "actionKeys": ["check", "revise"]}],
            "actions": [
                {"actionKey": "check", "operation": "query", "aiEnabled": True, "requiresConfirmation": False},
                {"actionKey": "revise", "operation": "update", "aiEnabled": True, "requiresConfirmation": True},
            ],
        }],
    }


def delivery():
    return {
        "schemaVersion": 1,
        "applicationSlug": "sample-review",
        "scope": "business_change",
        "scopeReason": "Test a synthetic assisted review journey",
        "journeys": [{
            "id": "completeness", "title": "Complete review", "baseline": "Manual comparison",
            "target": "Reduce repeated typing; duration measurement pending",
            "ownerDecision": "confirmed", "entryPoint": "on_demand", "delivery": "verified",
            "reason": "Synthetic verification fixture, not production evidence",
            "bindings": [
                {"moduleKey": "review", "pageKey": "items", "actionKey": "check"},
                {"moduleKey": "review", "pageKey": "items", "actionKey": "revise"},
            ],
            "platformChecks": [{
                "capability": "Assisted actions", "contractRef": "platform-contract.md",
                "deployed": "yes", "tenantEnabled": "yes", "actorAuthorized": "yes",
                "evidenceRefs": ["synthetic/reviewed-capability-record"],
            }],
            "confirmation": "Preview field differences; approval precedes write; rejection does not write",
            "acceptance": [{
                "scenario": "Query, correct a draft, confirm or reject, compare actual receipts",
                "status": "pass", "evidenceRefs": ["synthetic/receipts"],
            }],
            "gaps": [],
        }],
    }


def gap(status="open"):
    return {
        "owner": "SaaS", "problem": "Trigger not yet available", "acceptance": "Verify a real trigger",
        "fallback": "Keep on-demand launch", "status": status, "evidenceRefs": [],
    }


def delegation():
    return {
        "actorRef": "synthetic-test-role", "scope": "Read authorized review records",
        "expiresAt": "2026-09-01T17:00:00+08:00", "revocation": "Disable delegation in reviewed control",
        "limits": "One deduplicated attempt per event, reviewed budget limit",
        "approvalEvidence": "synthetic/delegation-receipt", "timezone": "Asia/Shanghai",
    }


def partial_delivery():
    document = delivery()
    future = copy.deepcopy(document["journeys"][0])
    future.update(id="future-background", entryPoint="background", delivery="blocked", bindings=[], gaps=[gap()])
    future["platformChecks"][0].update(deployed="unknown", tenantEnabled="unknown", actorAuthorized="unknown", evidenceRefs=[])
    future["acceptance"][0].update(status="not_run", evidenceRefs=[])
    document["journeys"].append(future)
    return document


class DeliveryValidationTests(unittest.TestCase):
    def test_verified_mapping_accepts_query_and_confirmed_write_without_mutation(self):
        document, app = delivery(), manifest()
        before = copy.deepcopy((document, app))
        self.assertEqual(MODULE.validate_delivery(document, app, True), [])
        self.assertEqual((document, app), before)

    def test_planned_document_retains_unknowns_and_unimplemented_action_as_gap(self):
        document = delivery()
        journey = document["journeys"][0]
        journey.update(ownerDecision="proposed", delivery="planned", bindings=[], gaps=[gap()])
        for field in ("deployed", "tenantEnabled", "actorAuthorized"):
            journey["platformChecks"][0][field] = "unknown"
        journey["platformChecks"][0]["evidenceRefs"] = []
        journey["acceptance"][0].update(status="not_run", evidenceRefs=[])
        self.assertEqual(MODULE.validate_delivery(document, manifest()), [])
        self.assertTrue(MODULE.validate_delivery(document, manifest(), True))

    def test_blocked_is_valid_design_but_not_verified(self):
        document = delivery()
        document["journeys"][0].update(delivery="blocked", gaps=[gap()])
        self.assertEqual(MODULE.validate_delivery(document, manifest()), [])
        self.assertTrue(MODULE.validate_delivery(document, manifest(), True))

    def test_selected_completion_does_not_require_future_blocked_work_to_be_done(self):
        document = partial_delivery()
        self.assertTrue(MODULE.validate_delivery(document, manifest(), True))
        self.assertEqual(MODULE.validate_delivery(document, manifest(), True, ["completeness"]), [])
        self.assertTrue(MODULE.validate_delivery(document, manifest(), True, ["future-background"]))
        self.assertTrue(MODULE.validate_delivery(document, manifest(), True, ["unknown"]))
        self.assertTrue(MODULE.validate_delivery(document, manifest(), True, ["completeness", "future-background"]))

    def test_selector_does_not_hide_malformed_unselected_evidence_or_bindings(self):
        document = partial_delivery()
        document["journeys"][1]["platformChecks"][0]["evidenceRefs"] = {"invalid": []}
        self.assertTrue(MODULE.validate_delivery(document, manifest(), True, ["completeness"]))
        document = partial_delivery()
        document["journeys"][1]["bindings"] = [{"moduleKey": "review", "pageKey": "items", "actionKey": "invented"}]
        self.assertTrue(MODULE.validate_delivery(document, manifest(), True, ["completeness"]))

    def test_selector_requires_explicit_verification_and_nonempty_valid_ids(self):
        self.assertTrue(MODULE.validate_delivery(delivery(), manifest(), False, ["completeness"]))
        for value in ([], "completeness", [None], [" "], [{}]):
            with self.subTest(value=value):
                self.assertTrue(MODULE.validate_delivery(delivery(), manifest(), True, value))

    def test_owner_manual_only_remains_an_explicit_valid_outcome(self):
        document = delivery()
        document["journeys"][0].update(
            delivery="not_applicable", ownerDecision="declined", bindings=[], platformChecks=[],
            acceptance=[], reason="Owner explicitly retained manual handling",
        )
        self.assertEqual(MODULE.validate_delivery(document, manifest(), True), [])
        document["journeys"][0]["bindings"] = delivery()["journeys"][0]["bindings"]
        self.assertTrue(MODULE.validate_delivery(document, manifest()))

    def test_confirmed_deterministic_design_can_be_not_applicable_without_faking_decline(self):
        document = delivery()
        document["journeys"][0].update(
            delivery="not_applicable", ownerDecision="confirmed", bindings=[], platformChecks=[],
            acceptance=[], reason="Owner approved deterministic arithmetic; model adds no benefit",
        )
        self.assertEqual(MODULE.validate_delivery(document, manifest(), True), [])
        self.assertEqual(document["journeys"][0]["ownerDecision"], "confirmed")
        document["journeys"][0]["reason"] = " "
        self.assertTrue(MODULE.validate_delivery(document, manifest()))

    def test_proposed_no_ai_design_is_not_a_confirmed_delivery(self):
        document = delivery()
        document["journeys"][0].update(delivery="not_applicable", ownerDecision="proposed", bindings=[])
        self.assertEqual(MODULE.validate_delivery(document, manifest()), [])
        self.assertTrue(MODULE.validate_delivery(document, manifest(), True))
        self.assertTrue(MODULE.validate_delivery(document, manifest(), True, ["completeness"]))

    def test_declined_decision_cannot_claim_an_active_ai_journey(self):
        for status in ("planned", "blocked", "verified"):
            with self.subTest(status=status):
                document = delivery()
                document["journeys"][0].update(delivery=status, ownerDecision="declined")
                self.assertTrue(MODULE.validate_delivery(document, manifest()))

    def test_out_of_scope_style_fix_does_not_require_a_journey(self):
        document = delivery()
        document.update(scope="out_of_scope", scopeReason="Fix a card margin only", journeys=[])
        self.assertEqual(MODULE.validate_delivery(document, manifest(), True), [])
        document["journeys"] = delivery()["journeys"]
        self.assertTrue(MODULE.validate_delivery(document, manifest()))

    def test_business_change_requires_journey_and_application_identity(self):
        for field, value in (("journeys", []), ("applicationSlug", "another-app"), ("scopeReason", " ")):
            with self.subTest(field=field):
                document = delivery()
                document[field] = value
                self.assertTrue(MODULE.validate_delivery(document, manifest()))

    def test_binding_must_resolve_in_the_same_module_and_page(self):
        for field in ("moduleKey", "pageKey", "actionKey"):
            with self.subTest(field=field):
                document = delivery()
                document["journeys"][0]["bindings"][0][field] = "unknown"
                self.assertTrue(MODULE.validate_delivery(document, manifest()))
        app = manifest()
        app["modules"].append({"moduleKey": "other", "pages": [], "actions": [app["modules"][0]["actions"].pop()]})
        self.assertTrue(MODULE.validate_delivery(delivery(), app))
        app = manifest()
        app["modules"][0]["pages"][0]["actionKeys"] = ["check"]
        self.assertTrue(MODULE.validate_delivery(delivery(), app))

    def test_disabled_or_truthy_not_boolean_ai_action_is_rejected(self):
        for enabled in (False, "true", 1, None):
            with self.subTest(enabled=enabled):
                app = manifest()
                app["modules"][0]["actions"][0]["aiEnabled"] = enabled
                self.assertTrue(MODULE.validate_delivery(delivery(), app))

    def test_all_assisted_mutations_require_real_confirmation_metadata(self):
        for operation in ("create", "update", "delete", "approve"):
            for confirmed in (False, "true", 1, None):
                with self.subTest(operation=operation, confirmed=confirmed):
                    app = manifest()
                    app["modules"][0]["actions"][1].update(operation=operation, requiresConfirmation=confirmed)
                    self.assertTrue(MODULE.validate_delivery(delivery(), app))

    def test_verified_requires_each_platform_dimension_and_evidence(self):
        for field in ("deployed", "tenantEnabled", "actorAuthorized"):
            for value in ("unknown", "no"):
                with self.subTest(field=field, value=value):
                    document = delivery()
                    document["journeys"][0]["platformChecks"][0][field] = value
                    self.assertTrue(MODULE.validate_delivery(document, manifest()))
        document = delivery()
        document["journeys"][0]["platformChecks"][0]["evidenceRefs"] = []
        self.assertTrue(MODULE.validate_delivery(document, manifest()))

    def test_verified_requires_owner_agreement_bindings_checks_and_passed_cases(self):
        for field, value in (("ownerDecision", "proposed"), ("bindings", []), ("platformChecks", []), ("acceptance", [])):
            with self.subTest(field=field):
                document = delivery()
                document["journeys"][0][field] = value
                self.assertTrue(MODULE.validate_delivery(document, manifest()))
        for status in ("fail", "not_run"):
            document = delivery()
            document["journeys"][0]["acceptance"][0]["status"] = status
            self.assertTrue(MODULE.validate_delivery(document, manifest()))
        document = delivery()
        document["journeys"][0]["acceptance"][0]["evidenceRefs"] = []
        self.assertTrue(MODULE.validate_delivery(document, manifest()))

    def test_verified_rejects_open_and_unsupported_gap_closure(self):
        for status in ("open", "closed"):
            document = delivery()
            document["journeys"][0]["gaps"] = [gap(status)]
            self.assertTrue(MODULE.validate_delivery(document, manifest()))
        document["journeys"][0]["gaps"][0]["evidenceRefs"] = ["synthetic/closure"]
        self.assertEqual(MODULE.validate_delivery(document, manifest()), [])

    def test_background_requires_delegation_and_recorded_acceptance(self):
        document = delivery()
        journey = document["journeys"][0]
        journey["entryPoint"] = "background"
        self.assertTrue(MODULE.validate_delivery(document, manifest()))
        journey["delegation"] = delegation()
        journey["acceptance"] = [{
            "scenario": "Synthetic trigger, deduplication, expiry, cancellation and recovery checked",
            "status": "pass", "evidenceRefs": ["synthetic/background-observations"],
        }]
        self.assertEqual(MODULE.validate_delivery(document, manifest()), [])
        for field in delegation():
            with self.subTest(missing=field):
                broken = copy.deepcopy(document)
                del broken["journeys"][0]["delegation"][field]
                self.assertTrue(MODULE.validate_delivery(broken, manifest()))

    def test_delegation_requires_beijing_business_zone_and_aware_valid_timestamp(self):
        document = delivery()
        document["journeys"][0].update(entryPoint="background", delegation=delegation())
        for value in ("2026-09-22T10:00:00", "2026-02-30T10:00:00+08:00", "2026-09-22", "2026-09-22T10:00:00+25:00"):
            with self.subTest(timestamp=value):
                document["journeys"][0]["delegation"]["expiresAt"] = value
                self.assertTrue(MODULE.validate_delivery(document, manifest()))
        document["journeys"][0]["delegation"] = delegation()
        document["journeys"][0]["delegation"]["timezone"] = "UTC"
        self.assertTrue(MODULE.validate_delivery(document, manifest()))

    def test_duplicate_ids_bindings_and_manifest_keys_are_rejected(self):
        document = delivery()
        document["journeys"].append(copy.deepcopy(document["journeys"][0]))
        self.assertTrue(MODULE.validate_delivery(document, manifest()))
        document = delivery()
        document["journeys"][0]["bindings"].append(copy.deepcopy(document["journeys"][0]["bindings"][0]))
        self.assertTrue(MODULE.validate_delivery(document, manifest()))
        for collection in ("modules", "pages", "actions"):
            app = manifest()
            items = app["modules"] if collection == "modules" else app["modules"][0][collection]
            items.append(copy.deepcopy(items[0]))
            self.assertTrue(MODULE.validate_delivery(delivery(), app))

    def test_malformed_root_and_nested_values_return_errors_instead_of_exceptions(self):
        for value in (None, [], 0, True, "bad", {}):
            with self.subTest(value=value):
                self.assertTrue(MODULE.validate_delivery(value, manifest()))
                self.assertTrue(MODULE.validate_delivery(delivery(), value))
        for field in MODULE.ROOT_FIELDS:
            document = delivery()
            document[field] = {"unexpected": []}
            self.assertTrue(MODULE.validate_delivery(document, manifest()))
        for field in MODULE.JOURNEY_FIELDS:
            document = delivery()
            document["journeys"][0][field] = {"unexpected": []}
            self.assertTrue(MODULE.validate_delivery(document, manifest()))
        for field in ("bindings", "platformChecks", "acceptance", "gaps"):
            for value in ([None], [{}], [True], ["unexpected"]):
                document = delivery()
                document["journeys"][0][field] = value
                self.assertTrue(MODULE.validate_delivery(document, manifest()))

    def test_malformed_manifest_arrays_and_keys_return_errors(self):
        for value in (None, {}, "bad", [None], [{}]):
            for collection in ("modules", "pages", "actions", "actionKeys"):
                with self.subTest(value=value, collection=collection):
                    app = manifest()
                    container = app if collection == "modules" else app["modules"][0]
                    if collection == "actionKeys":
                        container = container["pages"][0]
                    container[collection] = value
                    self.assertTrue(MODULE.validate_delivery(delivery(), app))

    def test_evidence_is_array_of_nonempty_strings_not_inline_data(self):
        for field in ("platformChecks", "acceptance"):
            for value in ("record", [" "], [{}], [True]):
                document = delivery()
                document["journeys"][0][field][0]["evidenceRefs"] = value
                self.assertTrue(MODULE.validate_delivery(document, manifest()))

    def test_schema_version_and_unknown_runtime_fields_are_rejected(self):
        for version in (True, 1.0, "1", 2):
            document = delivery()
            document["schemaVersion"] = version
            self.assertTrue(MODULE.validate_delivery(document, manifest()))
        document = delivery()
        document["schedule"] = {"providerKey": "synthetic-secret"}
        errors = MODULE.validate_delivery(document, manifest())
        self.assertTrue(errors)
        self.assertNotIn("synthetic-secret", json.dumps(errors))

    def test_error_messages_do_not_echo_untrusted_manifest_keys_or_payloads(self):
        app = manifest()
        app["modules"][0]["moduleKey"] = "synthetic-secret"
        app["modules"][0]["pages"] = "synthetic-secret"
        errors = MODULE.validate_delivery(delivery(), app)
        self.assertTrue(errors)
        self.assertNotIn("synthetic-secret", json.dumps(errors))

    def test_both_supported_manifest_versions_keep_their_revision(self):
        for revision in ("2.4", "2.5"):
            app = manifest()
            app["contractRevision"] = revision
            self.assertEqual(MODULE.validate_delivery(delivery(), app), [])
            self.assertEqual(app["contractRevision"], revision)

    def test_cli_reads_only_and_reports_json_disclaimer(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            documents = {"delivery.json": delivery(), "manifest.json": manifest()}
            for name, value in documents.items():
                (root / name).write_text(json.dumps(value), encoding="utf-8")
            before = {path.name: path.read_bytes() for path in root.iterdir()}
            args = [sys.executable, str(SCRIPT), "--delivery", str(root / "delivery.json"), "--manifest", str(root / "manifest.json"), "--require-verified"]
            result = subprocess.run(args, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            self.assertTrue(response["valid"])
            self.assertEqual(response["errors"], [])
            self.assertEqual(response["disclaimer"], MODULE.DISCLAIMER)
            self.assertEqual({path.name: path.read_bytes() for path in root.iterdir()}, before)
            (root / "delivery.json").write_text('{"secret": "synthetic-secret",', encoding="utf-8")
            result = subprocess.run(args, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(json.loads(result.stdout)["valid"])
            self.assertEqual(result.stderr, "")
            self.assertNotIn("synthetic-secret", result.stdout)

    def test_cli_bad_arguments_return_json_without_echoing_values(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--secret=synthetic-secret"], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(json.loads(result.stdout)["valid"])
        self.assertEqual(result.stderr, "")
        self.assertNotIn("synthetic-secret", result.stdout)

    def test_cli_selected_completion_allows_partial_delivery_but_rejects_bad_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "delivery.json").write_text(json.dumps(partial_delivery()), encoding="utf-8")
            (root / "manifest.json").write_text(json.dumps(manifest()), encoding="utf-8")
            args = [sys.executable, str(SCRIPT), "--delivery", str(root / "delivery.json"), "--manifest", str(root / "manifest.json")]
            for switches, expected in (
                (["--require-verified", "--journey", "completeness"], 0),
                (["--require-verified", "--journey", "future-background"], 1),
                (["--require-verified", "--journey", "completeness", "--journey", "future-background"], 1),
                (["--require-verified", "--journey", "unknown"], 1),
                (["--journey", "completeness"], 1),
            ):
                with self.subTest(switches=switches):
                    result = subprocess.run(args + switches, capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, expected, result.stderr)
                    self.assertEqual(json.loads(result.stdout)["valid"], expected == 0)
                    self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
