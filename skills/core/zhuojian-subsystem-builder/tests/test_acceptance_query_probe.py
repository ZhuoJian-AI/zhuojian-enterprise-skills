import pytest

from scripts.e2e_acceptance import validate_query_probe


@pytest.mark.parametrize("status", [401, 403])
def test_explicit_denial_never_claims_execution(status):
    result = validate_query_probe(status, {"detail": "Not authorized"}, expect_denied=True)
    assert result == "synthetic_identity_denied;authorized_execution_not_verified"


@pytest.mark.parametrize("status", [200, 400, 404, 422, 429, 500, 502, 503])
def test_denial_probe_does_not_hide_other_failures(status):
    with pytest.raises(SystemExit):
        validate_query_probe(status, {"detail": "error"}, expect_denied=True)


@pytest.mark.parametrize("result", [None, {}, {"detail": ""}, {"detail": "denied", "items": ["private"]}])
def test_denial_requires_error_only_payload(result):
    with pytest.raises(SystemExit):
        validate_query_probe(403, result, expect_denied=True)


def test_default_still_requires_success():
    assert validate_query_probe(200, {}, expect_denied=False) == "technical_path_executed_with_local_test_signature"
    with pytest.raises(SystemExit):
        validate_query_probe(403, {"detail": "denied"}, expect_denied=False)
