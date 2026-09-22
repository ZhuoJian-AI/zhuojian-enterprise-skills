import argparse
import copy
import importlib.util
import io
import json
import stat
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from urllib.error import HTTPError, URLError

import pytest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "runtime_capabilities_under_test",
    ROOT / "assets" / "admin-runtime" / "host" / "runtime_admin.py",
)
runtime = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runtime
SPEC.loader.exec_module(runtime)

SECRET = "zjrt_runtime-secret-that-must-not-appear-in-output"


def capability_payload():
    return {
        "schemaVersion": 1,
        "protocol": "zhuojian-platform-capabilities",
        "supportedContractRevisions": ["2.4", "2.5"],
        "assurance": "implementation-only",
        "requiresCurrentEmployeeAuthorization": True,
        "requiresHostCapabilityNegotiation": True,
        "doesNotGuaranteeAvailability": True,
        "features": {
            "assistantEntry": {
                "supported": True,
                "version": 1,
                "bridgeCapability": "assistant-open.v1",
                "endpoint": "/api/v1/terminal/applications/{application_id}/assistant-entry",
                "authentication": "employee-session",
                "mode": "draft-only",
            },
            "remoteActions": {"supported": True, "version": 2},
            "assistantSuggestions": {
                "supported": True,
                "version": 1,
                "bridgeCapability": "assistant-suggestions.v1",
                "authentication": "employee-session",
                "mode": "suggestion-only",
            },
            "assistantWorkflowGuidance": {
                "supported": True,
                "version": 1,
                "authentication": "employee-session",
                "mode": "foreground-read-only",
                "configEndpoint": "/api/v1/terminal/applications/{application_id}/page-assistance",
                "checkEndpoint": "/api/v1/terminal/applications/{application_id}/page-check",
            },
            "backgroundDelegation": {"supported": False},
            "unattendedExecution": {"supported": False},
        },
    }


@pytest.fixture
def dependencies():
    profile = {"platform": {"baseUrl": "https://Portal.Example.com/"}}
    path = mock.Mock()
    path.lstat.return_value = SimpleNamespace(st_uid=0, st_mode=stat.S_IFREG | 0o640)
    paths = runtime.Paths(runtime=path)
    response = mock.MagicMock()
    response.__enter__.return_value = response
    response.status = 200
    response.read.return_value = json.dumps(capability_payload()).encode()
    opener = mock.Mock()
    opener.open.return_value = response
    with (
        mock.patch.object(runtime, "load_runtime", return_value=profile),
        mock.patch.object(runtime, "runtime_registration_credential", return_value=SECRET) as credential,
        mock.patch.object(runtime.urllib.request, "build_opener", return_value=opener) as build,
        mock.patch.object(runtime, "atomic_write", side_effect=AssertionError("unexpected write")),
        mock.patch.object(runtime, "locked", side_effect=AssertionError("unexpected lock/write")),
        mock.patch.object(runtime, "run", side_effect=AssertionError("unexpected child command")),
    ):
        yield SimpleNamespace(
            paths=paths, profile=profile, response=response, opener=opener,
            build=build, credential=credential,
        )


def read(dependencies):
    return runtime.cmd_platform_capabilities(argparse.Namespace(), dependencies.paths)


def test_fixed_direct_get_uses_existing_credential_without_local_mutations(dependencies):
    assert read(dependencies) == capability_payload()
    request = dependencies.opener.open.call_args.args[0]
    assert request.full_url == "https://portal.example.com/api/v1/ecs-publisher/platform-capabilities"
    assert request.get_method() == "GET"
    assert request.data is None
    assert request.get_header("Authorization") == f"Bearer {SECRET}"
    assert dependencies.opener.open.call_count == 1
    assert dependencies.opener.open.call_args.kwargs == {"timeout": 20}
    handlers = dependencies.build.call_args.args
    assert handlers[0].proxies == {}
    assert isinstance(handlers[1], runtime.CapabilityNoRedirect)
    dependencies.response.read.assert_called_once_with(16 * 1024 + 1)


def test_output_projects_whitelist_including_nested_fields(dependencies):
    payload = capability_payload()
    payload["secret"] = SECRET
    payload["features"]["provider"] = {"apiKey": SECRET}
    payload["features"]["assistantEntry"]["modelKey"] = SECRET
    payload["features"]["assistantSuggestions"]["modelKey"] = SECRET
    payload["features"]["assistantWorkflowGuidance"]["modelKey"] = SECRET
    dependencies.response.read.return_value = json.dumps(payload).encode()
    assert read(dependencies) == capability_payload()


@pytest.mark.parametrize("status", [204, 302, 403])
def test_non_exception_non_200_response_is_still_not_success(dependencies, status):
    dependencies.response.status = status
    with pytest.raises(runtime.AdminError, match="unknown"):
        read(dependencies)
    dependencies.response.read.assert_not_called()


@pytest.mark.parametrize("location", ["https://other.example/", "https://portal.example.com/redirect"])
def test_redirect_handler_never_follows_even_same_origin(location):
    with pytest.raises(runtime.AdminError, match="must not redirect") as error:
        runtime.CapabilityNoRedirect().redirect_request(None, None, 302, SECRET, {}, location)
    assert SECRET not in str(error.value)


@pytest.mark.parametrize("status", [301, 302, 307, 308, 401, 403, 404, 429, 500, 503])
def test_http_errors_are_non_success_and_never_read_arbitrary_body(dependencies, status):
    body = mock.Mock()
    body.read.side_effect = AssertionError("must not read error body")
    dependencies.opener.open.side_effect = HTTPError(
        "https://portal.example.com/", status, SECRET, {}, body,
    )
    with pytest.raises(runtime.AdminError, match="unknown") as error:
        read(dependencies)
    assert str(status) in str(error.value)
    assert SECRET not in str(error.value)
    if status == 404:
        assert "unsupported" in str(error.value)
    body.read.assert_not_called()


@pytest.mark.parametrize("error", [URLError(SECRET), TimeoutError(SECRET), OSError(SECRET)])
def test_transport_failures_are_bounded_and_redacted(dependencies, error):
    dependencies.opener.open.side_effect = error
    with pytest.raises(runtime.AdminError, match="unknown") as caught:
        read(dependencies)
    assert SECRET not in str(caught.value)
    assert dependencies.opener.open.call_count == 1


@pytest.mark.parametrize("raw", [b"", b"not json", b"\xff", b"[]", b"null", b"x" * 16385])
def test_invalid_or_large_body_does_not_claim_support(dependencies, raw):
    dependencies.response.read.return_value = raw
    with pytest.raises(runtime.AdminError, match="unknown"):
        read(dependencies)


@pytest.mark.parametrize("key,value", [
    ("schemaVersion", True), ("schemaVersion", 2),
    ("protocol", SECRET), ("assurance", "verified"),
    ("requiresCurrentEmployeeAuthorization", False),
    ("requiresHostCapabilityNegotiation", 1),
    ("doesNotGuaranteeAvailability", False),
    ("supportedContractRevisions", [SECRET]),
    ("supportedContractRevisions", ["2.5", "2.5"]),
    ("supportedContractRevisions", []), ("features", []),
])
def test_unknown_schema_or_changed_assurance_is_rejected(dependencies, key, value):
    payload = capability_payload()
    payload[key] = value
    dependencies.response.read.return_value = json.dumps(payload).encode()
    with pytest.raises(runtime.AdminError, match="unknown") as error:
        read(dependencies)
    assert SECRET not in str(error.value)


@pytest.mark.parametrize("feature,key,value", [
    ("assistantEntry", "mode", "automatic"),
    ("assistantEntry", "endpoint", "https://other.example/"),
    ("assistantEntry", "authentication", "runtime-credential"),
    ("assistantEntry", "version", True),
    ("assistantSuggestions", "mode", "automatic"),
    ("assistantSuggestions", "authentication", "runtime-credential"),
    ("assistantSuggestions", "bridgeCapability", "assistant-open.v1"),
    ("assistantSuggestions", "version", True),
    ("assistantSuggestions", "supported", "true"),
    ("assistantWorkflowGuidance", "supported", "true"),
    ("assistantWorkflowGuidance", "version", True),
    ("assistantWorkflowGuidance", "mode", "background"),
    ("assistantWorkflowGuidance", "authentication", "runtime-credential"),
    ("assistantWorkflowGuidance", "configEndpoint", "https://other.example/"),
    ("assistantWorkflowGuidance", "checkEndpoint", "/arbitrary-run"),
    ("backgroundDelegation", "supported", True),
    ("unattendedExecution", "supported", True),
])
def test_unknown_or_unsafe_feature_semantics_require_new_cli(dependencies, feature, key, value):
    payload = capability_payload()
    payload["features"][feature][key] = value
    dependencies.response.read.return_value = json.dumps(payload).encode()
    with pytest.raises(runtime.AdminError, match="unknown"):
        read(dependencies)


@pytest.mark.parametrize("platform", [None, {}, {"baseUrl": "http://portal.example.com"},
    {"baseUrl": "https://portal.example.com/path"}, {"baseUrl": "https://user@portal.example.com"}])
def test_destination_must_come_from_explicit_valid_runtime_profile(dependencies, platform):
    dependencies.profile["platform"] = platform
    with pytest.raises(runtime.AdminError):
        read(dependencies)
    dependencies.credential.assert_not_called()
    dependencies.opener.open.assert_not_called()


@pytest.mark.parametrize("mode", [stat.S_IFREG | 0o666, stat.S_IFLNK | 0o600])
def test_unsafe_runtime_profile_is_rejected_before_reading_credential(dependencies, mode):
    dependencies.paths.runtime.lstat.return_value.st_mode = mode
    with pytest.raises(runtime.AdminError):
        read(dependencies)
    dependencies.credential.assert_not_called()
    dependencies.opener.open.assert_not_called()


def test_linux_rejects_non_root_profile_owner(dependencies):
    dependencies.paths.runtime.lstat.return_value.st_uid = 1000
    with mock.patch.object(runtime.os, "name", "posix"):
        with pytest.raises(runtime.AdminError, match="root-owned"):
            read(dependencies)
    dependencies.credential.assert_not_called()


def test_header_injection_in_credential_is_rejected(dependencies):
    dependencies.credential.return_value = SECRET + "\nInjected: yes"
    with pytest.raises(runtime.AdminError, match="credential is invalid"):
        read(dependencies)
    dependencies.opener.open.assert_not_called()


def test_command_has_no_destination_override_and_keeps_existing_commands():
    args = runtime.parser().parse_args(["platform-capabilities"])
    assert args.func is runtime.cmd_platform_capabilities
    with pytest.raises(SystemExit):
        runtime.parser().parse_args(["platform-capabilities", "--url", "https://other.example/"])
    assert runtime.parser().parse_args(["doctor"]).func is runtime.cmd_doctor
    assert runtime.parser().parse_args(["deploy", "sample-app"]).func is runtime.cmd_deploy


def test_cli_404_exits_nonzero_and_never_prints_secrets(dependencies, capsys):
    dependencies.opener.open.side_effect = HTTPError("https://portal.example.com/", 404, SECRET, {}, io.BytesIO(SECRET.encode()))
    with mock.patch.object(runtime, "PATHS", dependencies.paths):
        assert runtime.main(["platform-capabilities"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unsupported" in captured.err
    assert SECRET not in captured.err
    assert json.loads(captured.err)["ok"] is False


def test_cli_success_prints_only_the_sanitized_response(dependencies, capsys):
    payload = capability_payload()
    payload["diagnostics"] = SECRET
    dependencies.response.read.return_value = json.dumps(payload).encode()
    with mock.patch.object(runtime, "PATHS", dependencies.paths):
        assert runtime.main(["platform-capabilities"]) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == capability_payload()
    assert captured.err == ""
    assert SECRET not in captured.out


def test_success_does_not_mutate_the_received_declaration():
    payload = capability_payload()
    before = copy.deepcopy(payload)
    projected = runtime.sanitized_platform_capabilities(payload)
    projected["features"]["assistantEntry"]["mode"] = "changed"
    assert payload == before


@pytest.mark.parametrize("declaration", [None, {"supported": False}])
def test_missing_or_explicitly_unsupported_suggestions_do_not_break_old_backend(dependencies, declaration):
    payload = capability_payload()
    if declaration is None:
        del payload["features"]["assistantSuggestions"]
    else:
        payload["features"]["assistantSuggestions"] = declaration
    dependencies.response.read.return_value = json.dumps(payload).encode()
    result = read(dependencies)
    assert result["features"]["assistantSuggestions"] == {"supported": False}
    assert result["features"]["assistantEntry"]["mode"] == "draft-only"


@pytest.mark.parametrize("declaration", [None, [], {}, {"supported": True}, {"supported": 1}])
def test_present_but_invalid_suggestions_are_not_silently_reported_as_supported(dependencies, declaration):
    payload = capability_payload()
    payload["features"]["assistantSuggestions"] = declaration
    dependencies.response.read.return_value = json.dumps(payload).encode()
    with pytest.raises(runtime.AdminError, match="unknown"):
        read(dependencies)


@pytest.mark.parametrize("declaration", [None, {"supported": False}])
def test_old_backend_does_not_invent_workflow_support(dependencies, declaration):
    payload = capability_payload()
    if declaration is None:
        del payload["features"]["assistantWorkflowGuidance"]
    else:
        payload["features"]["assistantWorkflowGuidance"] = declaration
    dependencies.response.read.return_value = json.dumps(payload).encode()
    result = read(dependencies)
    assert result["features"]["assistantWorkflowGuidance"] == {"supported": False}
    assert result["features"]["assistantEntry"]["mode"] == "draft-only"


@pytest.mark.parametrize("declaration", [None, [], {}, {"supported": True}, {"supported": 1}])
def test_invalid_workflow_feature_is_unknown_not_usable(dependencies, declaration):
    payload = capability_payload()
    payload["features"]["assistantWorkflowGuidance"] = declaration
    dependencies.response.read.return_value = json.dumps(payload).encode()
    with pytest.raises(runtime.AdminError, match="unknown"):
        read(dependencies)


def test_legacy_backend_without_either_optional_feature_keeps_original_capabilities():
    payload = capability_payload()
    del payload["features"]["assistantWorkflowGuidance"]
    del payload["features"]["assistantSuggestions"]
    result = runtime.sanitized_platform_capabilities(payload)
    assert result["features"]["assistantWorkflowGuidance"] == {"supported": False}
    assert result["features"]["assistantSuggestions"] == {"supported": False}
    assert result["supportedContractRevisions"] == ["2.4", "2.5"]
