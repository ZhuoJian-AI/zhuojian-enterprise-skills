"""Exercise the public validator CLI used before enterprise development."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
ORG = "00000000-0000-4000-8000-000000000001"


def profile():
    return {
        "organizationId": ORG, "environment": "staging",
        "capabilities": {"fileStorage": True, "objectStorage": True},
        "fileStorage": {"provider": "aliyun-oss", "mode": "oss-gateway", "verified": True},
        "objectStorage": {
            "provider": "aliyun-oss", "mode": "gateway-api-v1", "bucket": "shared-company-files",
            "region": "cn-hangzhou", "namespaceMode": "enterprise-v1",
            "rootPrefix": f"enterprises/{ORG}/staging/apps",
            "gatewayBaseUrl": "http://zhuojian-storage-gateway:8080",
            "credentialRef": "/etc/zhuojian/oss-gateway.env", "verified": True,
        },
    }


def validate(value):
    return subprocess.run(
        [sys.executable, "-B", str(ROOT / "scripts/validate_storage_profile.py"),
         "--runtime-profile", "-", "--require-mode", "oss"],
        input=json.dumps(value), text=True, capture_output=True,
        encoding="utf-8", env={**__import__("os").environ, "PYTHONUTF8": "1"},
    )


@pytest.mark.parametrize("environment", ["development", "staging", "production"])
def test_enterprise_profile_passes_real_validation_cli(environment):
    value = profile()
    value["environment"] = environment
    value["objectStorage"]["rootPrefix"] = f"enterprises/{ORG}/{environment}/apps"
    result = validate(value)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "STORAGE PROFILE VALIDATION PASS" in result.stdout


@pytest.mark.parametrize("explicit", [False, True])
def test_legacy_apps_profile_needs_no_new_identity_fields(explicit):
    value = profile()
    del value["organizationId"], value["environment"]
    value["objectStorage"]["rootPrefix"] = "apps"
    if explicit:
        value["objectStorage"]["namespaceMode"] = "legacy-apps"
    else:
        del value["objectStorage"]["namespaceMode"]
    result = validate(value)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("section,key,value", [
    ("objectStorage", "rootPrefix", "apps"),
    ("objectStorage", "rootPrefix", "enterprises/00000000-0000-4000-8000-000000000002/staging/apps"),
    ("objectStorage", "rootPrefix", f"enterprises/{ORG}/production/apps"),
    ("objectStorage", "rootPrefix", f"enterprises/{ORG}/staging/apps/../other"),
    ("objectStorage", "namespaceMode", "unknown"),
    ("objectStorage", "namespaceMode", None),
    ("objectStorage", "namespaceMode", []),
    (None, "organizationId", None),
    (None, "organizationId", "not-a-uuid"),
    (None, "environment", None),
    (None, "environment", "another-environment"),
    (None, "environment", []),
])
def test_wrong_or_incomplete_namespace_fails_closed(section, key, value):
    candidate = profile()
    (candidate[section] if section else candidate)[key] = value
    result = validate(candidate)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "STORAGE PROFILE VALIDATION FAILED" in result.stdout
    assert "Traceback" not in result.stderr
