#!/usr/bin/env python3
"""Switch a restored, fenced candidate's OSS scope; never connect to its source.

The administrator supplies evidence from the final frozen object enumeration.
This is deliberately separate from configure-oss-gateway and normal releases.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import subprocess
import tempfile
import time

import runtime_admin as ra


class MigrationError(RuntimeError):
    pass


GATEWAY = "zhuojian-storage-gateway"
REQUIRED_UNITS = {"nginx.service", "cron.service", "zhuojian-backup.timer", "zhuojian-backup.service"}
PROBE_CHECKS = {
    "anonymousReadDenied", "put", "get", "delete", "twoApplicationIsolation",
    "temporaryCredentialsRevoked", "outsidePrefixDenied",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MigrationError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def secure_read(path: Path) -> bytes:
    ra.secure_file_metadata(path, "migration input")
    return path.read_bytes()


def state_read(path: Path) -> bytes:
    ra.assert_plain_file(path)
    info = path.lstat()
    require((os.name == "nt" or info.st_uid == 0) and not stat.S_IMODE(info.st_mode) & 0o022, "managed state must be root-owned and not group/world writable")
    return path.read_bytes()


def parse_manifest(raw: bytes, *, check_age: bool = True) -> dict:
    try:
        item = json.loads(raw)
        require(item["schemaVersion"] == 1, "unsupported manifest schema")
        require(bool(re.fullmatch(r"[0-9a-f]{32}", item["operationId"])), "invalid operation ID")
        stamp = dt.datetime.fromisoformat(item["capturedAt"].replace("Z", "+00:00"))
        age = (dt.datetime.now(dt.timezone.utc) - stamp).total_seconds()
        if check_age:
            require(0 <= age <= 7200, "final frozen manifest must be at most two hours old")
        require(item["sourceWritesFrozen"] is True, "source writes are not frozen")
        source, target = item["source"], item["target"]
        for side in (source, target):
            require(side["enumerationComplete"] is True, "incomplete object enumeration")
            require(side["versioning"] == "Disabled", "versioned buckets need a separate migration")
            require(bool(re.fullmatch(r"[0-9a-f]{32}", side["machineId"])), "invalid machine identity")
            ra.validate_management_host(side["host"])
            require(bool(ra.BUCKET_RE.fullmatch(side["bucket"])), "invalid bucket")
            require(ra.normalize_aliyun_region(side["region"]) == side["region"], "region must be canonical")
        require(source["machineId"] != target["machineId"] and source["host"] != target["host"], "source and target must be different hosts")
        require((source["bucket"], source["region"]) != (target["bucket"], target["region"]), "scope did not change")
        require(bool(re.fullmatch(r"[0-9a-f]{64}", source["runtimeSha256"])), "invalid runtime digest")
        require(set(item["identity"]) == {"enterpriseKey", "organizationId", "runtimeId"}, "missing runtime identity")
        require(all(isinstance(v, str) and v for v in item["identity"].values()), "empty runtime identity")
        releases = item["releaseSha256"]
        require(isinstance(releases, dict) and bool(releases), "release inventory is required")
        for slug, digest in releases.items():
            ra.validate_slug(slug)
            require(bool(re.fullmatch(r"[0-9a-f]{64}", digest)), "invalid release digest")
        units = item["stoppedUnits"]
        require(isinstance(units, list) and REQUIRED_UNITS.issubset(units), "missing mandatory write fences")
        require(all(isinstance(x, str) and re.fullmatch(r"[A-Za-z0-9@_.-]+\.(?:service|timer)", x) for x in units), "invalid unit name")
        keys, total = set(), 0
        for obj in item["objects"]:
            key = obj["key"]
            require(isinstance(key, str) and key.startswith("apps/") and key not in keys, "invalid or duplicate object key")
            keys.add(key)
            size = obj["size"]
            require(isinstance(size, int) and not isinstance(size, bool) and size >= 0, "invalid object size")
            left, right = obj["source"], obj["target"]
            require(left["size"] == size == right["size"], "object size differs")
            require(isinstance(left["metadata"], dict) and left["metadata"] == right["metadata"], "object content metadata differs")
            require(all(isinstance(k, str) and isinstance(v, str) for k, v in left["metadata"].items()), "invalid content metadata")
            require(isinstance(left["etag"], str) and bool(left["etag"]) and isinstance(right["etag"], str) and bool(right["etag"]), "missing ETag evidence")
            crc = left.get("crc64")
            digest = left.get("sha256")
            crc_ok = isinstance(crc, str) and bool(re.fullmatch(r"\d+", crc)) and crc == right.get("crc64")
            sha_ok = isinstance(digest, str) and bool(re.fullmatch(r"[0-9a-f]{64}", digest)) and digest == right.get("sha256")
            require(crc_ok or sha_ok, "object content checksum differs or is missing")
            total += size
        require(len(keys) == item["objectCount"] == source["objectCount"] == target["objectCount"], "enumerated object counts differ")
        require(total == item["totalBytes"] == source["totalBytes"] == target["totalBytes"], "enumerated object byte counts differ")
        return item
    except (KeyError, TypeError, ValueError, AttributeError, ra.AdminError) as exc:
        raise MigrationError("invalid migration manifest") from exc


def check_env(data: bytes, scope: dict) -> None:
    values = {}
    try:
        for line in data.decode("utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            require(key not in values, "duplicate gateway configuration key")
            values[key] = value.strip().strip("\"'")
        region = scope["region"]
        require(values.get("OSS_BUCKET") == scope["bucket"], "gateway bucket does not match evidence")
        require(values.get("OSS_ENDPOINT") in {f"https://oss-{region}.aliyuncs.com", f"https://oss-{region}-internal.aliyuncs.com"}, "gateway endpoint does not match region")
        require(bool(values.get("OSS_ACCESS_KEY_ID")) and bool(values.get("OSS_ACCESS_KEY_SECRET")), "gateway credentials are missing")
    except (UnicodeError, ValueError) as exc:
        raise MigrationError("invalid gateway configuration") from exc


class Host:
    """All effects are local to the restored candidate; child output stays private."""
    def command(self, *argv: str, timeout: int = 120) -> str:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        require(result.returncode == 0, "local migration command failed")
        return result.stdout

    def fenced(self, manifest: dict) -> None:
        machine = Path("/etc/machine-id").read_text().strip()
        require(machine == manifest["target"]["machineId"], "this is not the target host")
        for unit in manifest["stoppedUnits"]:
            state = self.command("systemctl", "show", unit, "--property=ActiveState", "--value").strip()
            require(state in {"inactive", "failed"}, "a fenced unit is active")
        running = self.command("docker", "ps", "--format", "{{.Names}}").splitlines()
        require(set(running) <= {GATEWAY}, "target business containers must be stopped")
        cutoff = dt.datetime.fromisoformat(manifest["capturedAt"].replace("Z", "+00:00"))
        for name in self.command("docker", "ps", "-a", "--format", "{{.Names}}").splitlines():
            if name == GATEWAY:
                continue
            state = json.loads(self.command("docker", "inspect", "--format", "{{json .State}}", name))
            started = dt.datetime.fromisoformat(state["StartedAt"].replace("Z", "+00:00"))
            require(not state["Running"] and started < cutoff, "a business container started after the frozen inventory; reconcile target writes first")

    def gateway_info(self) -> dict:
        data = json.loads(self.command("docker", "inspect", GATEWAY))[0]
        labels = data["Config"].get("Labels") or {}
        require(labels.get("com.docker.compose.project") == GATEWAY, "gateway is not managed by the expected compose project")
        networks = sorted(data["NetworkSettings"]["Networks"])
        require(all(x == "zhuojian-storage" or x.startswith("zhuojian-storage-") for x in networks), "gateway has unrecognized networks")
        require("zhuojian-storage" in networks, "gateway management network is missing")
        require(not data["HostConfig"].get("PortBindings"), "gateway must not publish host ports")
        return {"image": data["Image"], "networks": networks, "running": data["State"]["Running"]}

    def stop(self) -> None:
        def missing() -> bool:
            result = subprocess.run(["docker", "container", "inspect", GATEWAY], capture_output=True, text=True, timeout=30, check=False)
            if result.returncode == 0:
                return False
            absent = result.returncode == 1 and result.stdout.strip() in {"", "[]"} and re.fullmatch(
                rf"Error(?: response from daemon)?: No such (?:container|object): {GATEWAY}", result.stderr.strip()
            )
            require(bool(absent), "cannot establish gateway presence; Docker inspection failed")
            return True
        if missing():
            return
        result = subprocess.run(["docker", "stop", GATEWAY], capture_output=True, text=True, timeout=120, check=False)
        if result.returncode:
            # Compose may have removed the old container before an interrupted
            # replacement. Only positively identified absence is recoverable.
            require(missing(), "could not stop the gateway for restoration")

    def recreate(self, before: dict) -> None:
        require(bool(re.fullmatch(r"sha256:[0-9a-f]{64}", before["image"])), "gateway image must be immutable")
        with tempfile.TemporaryDirectory(prefix="zhuojian-oss-image-") as directory:
            override = Path(directory) / "compose.json"
            ra.atomic_json(override, {"services": {GATEWAY: {"image": before["image"]}}}, 0o600)
            self.command("docker", "compose", "-p", GATEWAY, "-f", "/opt/zhuojian/storage-gateway/compose.yaml", "-f", str(override), "up", "-d", "--no-build", "--pull", "never", "--force-recreate", GATEWAY)
        after = self.gateway_info()
        require(after["image"] == before["image"], "gateway image changed during scope migration")
        for network in before["networks"]:
            if network not in after["networks"]:
                self.command("docker", "network", "connect", network, GATEWAY)
        for _ in range(45):
            value = self.command("docker", "inspect", "--format", "{{if .State.Health}}{{.State.Health.Status}}{{end}}", GATEWAY).strip()
            if value == "healthy":
                return
            time.sleep(2)
        raise MigrationError("candidate gateway did not become healthy")

    def probe(self, scope: dict) -> None:
        data = json.loads(self.command(str(ra.STORAGE_ADMIN), "probe", "--expected-bucket", scope["bucket"], "--expected-region", scope["region"], timeout=600))
        require(data.get("ok") is True and all(data.get("checks", {}).get(k) is True for k in PROBE_CHECKS), "candidate gateway acceptance failed")


def registry_backup(source: Path, target: Path) -> None:
    state_read(source)
    with contextlib.closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as incoming:
        with contextlib.closing(sqlite3.connect(target)) as outgoing:
            incoming.backup(outgoing)
    os.chmod(target, 0o600)


def restore(directory: Path, journal: dict, paths: ra.Paths, env: Path, registry: Path, host: Host) -> None:
    payloads = {name: secure_read(directory / name) for name in ("runtime.json", "oss-gateway.env", "registry.sqlite3")}
    for name, destination in journal["appEnvPaths"].items():
        target = Path(destination)
        require(target.parent in {paths.storage_apps, paths.apps_env} and target.name.endswith(".storage.env"), "unexpected app identity backup path")
        ra.validate_slug(target.name.removesuffix(".storage.env"))
        require(name == target.name, "unexpected app identity backup name")
        payloads[name] = secure_read(directory / name)
    require(all(sha(data) == journal["backupSha256"][name] for name, data in payloads.items()), "migration backup digest differs")
    host.stop()
    for name, target in (("runtime.json", paths.runtime), ("oss-gateway.env", env), ("registry.sqlite3", registry)):
        data = payloads[name]
        if target == registry:
            for suffix in ("-wal", "-shm"):
                extra = Path(str(registry) + suffix)
                if extra.exists() or extra.is_symlink():
                    state_read(extra)
                    extra.unlink()
        ra.atomic_write(target, data, 0o600)
    for name, destination in journal["appEnvPaths"].items():
        ra.atomic_write(Path(destination), payloads[name], 0o600)
    host.recreate(journal["gateway"])
    if not journal["gateway"]["running"]:
        host.stop()
    journal["phase"] = "rolled-back"
    ra.atomic_json(directory / "journal.json", journal, 0o600)


def migrate(raw: bytes, candidate_env: bytes, paths: ra.Paths, env: Path, registry: Path, host: Host, *, rollback: bool = False) -> dict:
    manifest = parse_manifest(raw, check_age=not rollback)
    operation = manifest["operationId"]
    host.fenced(manifest)
    directory = paths.backups / "oss-scope" / operation
    state = directory / "journal.json"
    if state.exists():
        journal = json.loads(secure_read(state))
        require(journal["manifestSha256"] == sha(raw), "operation already belongs to different evidence")
        if journal["phase"] == "committed" and not rollback:
            require(sha(secure_read(paths.runtime)) == journal["newRuntimeSha256"] and sha(secure_read(env)) == journal["newEnvSha256"], "committed state has drifted")
            return {"ok": True, "changed": False, "phase": "committed", "operationId": operation}
        if journal["phase"] == "rolled-back":
            return {"ok": True, "changed": False, "phase": "rolled-back", "operationId": operation}
        restore(directory, journal, paths, env, registry, host)
        return {"ok": True, "changed": True, "phase": "rolled-back", "operationId": operation}
    require(not rollback, "no migration journal exists for rollback")
    require(not directory.exists(), "incomplete preparation directory requires administrator inspection")
    original = state_read(paths.runtime)
    require(sha(original) == manifest["source"]["runtimeSha256"], "restored source Runtime differs")
    profile = json.loads(original)
    require(all(profile.get(k) == v for k, v in manifest["identity"].items()), "restored Runtime identity differs")
    require(profile.get("network", {}).get("managementAccess", {}).get("host") == manifest["source"]["host"], "restored source management host differs")
    ra.load_runtime(paths)
    scope = profile.get("objectStorage", {})
    require(scope.get("bucket") == manifest["source"]["bucket"] and scope.get("region") == manifest["source"]["region"] and scope.get("rootPrefix") == "apps", "source OSS scope differs")
    releases, secrets = {}, {}
    for marker in sorted(paths.deployments.glob("*/release.json")):
        data = state_read(marker)
        item = json.loads(data)
        require(item.get("managedBy") == ra.MANAGED_BY, "unmanaged release found")
        require(item.get("storageRotation") is None and item.get("releaseSwitch") is None, "release transition is pending")
        releases[marker.parent.name] = sha(data)
        if item.get("storageMode") == ra.OSS_STORAGE_MODE:
            require(item.get("enterpriseKey") == profile["enterpriseKey"], "release enterprise identity differs")
            secret = ra.installed_storage_env_path(marker.parent.name, paths, expected=item.get("storageEnvFile"))
            secrets[str(secret)] = sha(secure_read(secret))
    require(releases == manifest["releaseSha256"] and bool(secrets), "release inventory differs or no OSS releases exist")
    old_env = secure_read(env)
    check_env(old_env, manifest["source"])
    check_env(candidate_env, manifest["target"])
    before = host.gateway_info()
    host.stop()
    try:
        directory.mkdir(parents=True, mode=0o700)
        ra.atomic_write(directory / "runtime.json", original, 0o600)
        ra.atomic_write(directory / "oss-gateway.env", old_env, 0o600)
        registry_backup(registry, directory / "registry.sqlite3")
        app_paths = {}
        for secret in secrets:
            path = Path(secret)
            ra.atomic_write(directory / path.name, secure_read(path), 0o600)
            app_paths[path.name] = secret
        journal = {
            "phase": "prepared", "manifestSha256": sha(raw), "gateway": before,
            "appEnvPaths": app_paths,
            "backupSha256": {name: sha(secure_read(directory / name)) for name in ("runtime.json", "oss-gateway.env", "registry.sqlite3", *app_paths)},
        }
        ra.atomic_json(state, journal, 0o600)
    except BaseException:
        if before["running"]:
            host.recreate(before)
        raise
    try:
        ra.atomic_write(env, candidate_env, 0o600)
        host.recreate(before)
        host.probe(manifest["target"])
        host.fenced(manifest)
        require(all(sha(secure_read(Path(k))) == v for k, v in secrets.items()), "existing app storage identities changed")
        require({p.parent.name: sha(state_read(p)) for p in paths.deployments.glob("*/release.json")} == releases, "release inventory changed during migration")
        updated = copy.deepcopy(profile)
        updated["objectStorage"].update(bucket=manifest["target"]["bucket"], region=manifest["target"]["region"])
        updated["verifiedAt"] = ra.utc_now()
        ra.atomic_json(paths.runtime, updated, 0o600)
        ra.load_runtime(paths)
        journal.update(phase="committed", newRuntimeSha256=sha(secure_read(paths.runtime)), newEnvSha256=sha(candidate_env))
        ra.atomic_json(state, journal, 0o600)
    except BaseException:
        restore(directory, journal, paths, env, registry, host)
        raise
    return {"ok": True, "changed": True, "phase": "committed", "operationId": operation, "businessStarted": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--candidate-env", type=Path)
    parser.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    try:
        require(hasattr(os, "geteuid") and os.geteuid() == 0, "migration must run as root on the candidate")
        require(args.rollback or args.candidate_env is not None, "candidate env file is required")
        raw = secure_read(args.manifest)
        candidate = secure_read(args.candidate_env) if args.candidate_env else b""
        with ra.locked(ra.PATHS):
            result = migrate(raw, candidate, ra.PATHS, ra.STORAGE_CREDENTIAL, Path("/var/lib/zhuojian-storage-gateway/registry.sqlite3"), Host(), rollback=args.rollback)
        print(json.dumps(result))
        return 0
    except MigrationError as exc:
        # These messages are fixed literals; never attach child output or input.
        print(json.dumps({"ok": False, "message": str(exc), "businessStarted": False}))
        return 1
    except (ra.AdminError, OSError, ValueError, KeyError, subprocess.SubprocessError):
        # Exception strings and child output could contain secret-file content.
        print(json.dumps({"ok": False, "message": "OSS candidate migration refused or failed; keep business fenced and inspect the root-only migration journal."}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
