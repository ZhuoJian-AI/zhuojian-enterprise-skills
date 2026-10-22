from copy import deepcopy

from scripts.e2e_acceptance import pending_authorization_results


def test_technical_preflight_never_claims_authorization_boundaries_passed():
    manifest = {"applicationSlug": "example", "health": "healthy", "authorization_acceptance_pass": True,
                "authorization_results": [{"passed": True}], "modules": []}
    original = deepcopy(manifest)
    results = pending_authorization_results(manifest)
    assert manifest == original
    assert {row["check"] for row in results} == {
        "exact_business_route_binding", "paired_role_work_departments", "department_lifecycle_revocation",
        "import_create_update_atomicity", "business_boundary_preservation", "web_api_ai_file_parity",
    }
    assert all(row["applicationSlug"] == "example" and row["passed"] is None and row["failures"] for row in results)


def test_pending_import_and_lifecycle_checks_are_not_inferred_away_by_manifest():
    # A Manifest cannot enumerate private REST import paths, tickets or old sessions.
    for modules in ([], [{"moduleKey": "records", "actions": [{"operation": "query"}]}]):
        results = pending_authorization_results({"modules": modules})
        assert len(results) == 6
        assert all(row["passed"] is None for row in results)
