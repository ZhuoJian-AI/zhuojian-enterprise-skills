"""Read-only status; deliberately not a replacement for Runtime doctor."""
import json
import pathlib
import shutil
import stat


def audit(profile, credential):
    state = profile.get("initialization", {})
    metadata = credential.stat() if credential.is_file() and not credential.is_symlink() else None
    identity_ok = profile.get("enterpriseKey") == "zhuojian" and profile.get("runtimeId") == "zhuojian-hz-shared-01"
    return {
        "enterpriseIdentityMatches": identity_ok,
        "registrationCredentialPrivate": bool(metadata and metadata.st_uid == 0 and stat.S_IMODE(metadata.st_mode) == 0o600),
        "initializationStatus": state.get("status", "unknown"),
        "runtimeDoctorInstalled": shutil.which("zhuojian-runtime") is not None,
        "declaredReady": state.get("ready") is True,
        "acceptance": "not-proven-by-this-read-only-audit",
    }


if __name__ == "__main__":
    profile = json.loads(pathlib.Path("/etc/zhuojian/runtime.json").read_text())
    result = audit(profile, pathlib.Path("/etc/zhuojian/runtime-registration.key"))
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result["enterpriseIdentityMatches"] and result["registrationCredentialPrivate"] else 1)
