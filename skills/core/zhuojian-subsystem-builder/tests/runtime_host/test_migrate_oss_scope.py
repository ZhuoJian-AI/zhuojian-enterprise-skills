import copy
import contextlib
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HOST_DIR = Path(__file__).resolve().parents[2] / "assets/admin-runtime/host"
sys.path.insert(0, str(HOST_DIR))
import migrate_oss_scope as migration

ra = migration.ra


class FakeHost:
    def __init__(self):
        self.calls = []
        self.fail_probe = False
        self.during_probe = None
        self.business_running = False

    def fenced(self, manifest):
        self.calls.append("fenced")
        migration.require(not self.business_running, "business running")

    def gateway_info(self):
        return {"image": "sha256:" + "a" * 64, "networks": ["zhuojian-storage", "zhuojian-storage-sample"], "running": True}

    def stop(self):
        self.calls.append("stop")

    def recreate(self, before):
        self.calls.append("recreate")

    def probe(self, scope):
        self.calls.append("probe")
        if self.during_probe:
            self.during_probe()
        migration.require(not self.fail_probe, "probe failed")


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.paths = ra.Paths(**{name: root / name for name in ra.Paths.__dataclass_fields__})
        self.paths.deployments.mkdir()
        self.paths.storage_apps.mkdir()
        self.paths.apps_env.mkdir()
        self.env = root / "gateway.env"
        self.registry = root / "registry.sqlite3"
        self.secret = self.paths.storage_apps / "sample.storage.env"
        self.secret.write_bytes(b"FILE_STORAGE_TOKEN=fixture-identity\n")
        self.secret.chmod(0o600)
        self.addCleanup(mock.patch.stopall)
        # Windows cannot represent POSIX uid/mode; production metadata is covered
        # by the existing Runtime host suite and is never bypassed by the CLI.
        if os.name == "nt":
            mock.patch.object(ra, "secure_file_metadata", return_value={}).start()
            mock.patch.object(migration, "state_read", side_effect=lambda p: p.read_bytes()).start()
        self.profile = {
            "schemaVersion": 2, "enterpriseKey": "aifabei", "runtimeId": "aifabei-hk-01",
            "organizationId": "00000000-0000-4000-8000-000000000001",
            "network": {"managementAccess": {"host": "8.218.208.205"}},
            "domains": {"suffix": "hk01.example.com"},
            "deployment": {
                "repositoriesRoot": str(self.paths.repositories), "deploymentsRoot": str(self.paths.deployments),
                "dataRoot": str(self.paths.data), "backupsRoot": str(self.paths.backups),
                "nginxConfigRoot": str(self.paths.nginx), "registrationCredentialRef": str(self.paths.credential),
            },
            "fileStorage": {"provider": "aliyun-oss", "mode": "oss-gateway", "verified": True},
            "capabilities": {"objectStorage": True},
            "objectStorage": {"provider": "aliyun-oss", "mode": "gateway-api-v1", "bucket": "source-files", "region": "cn-hongkong", "rootPrefix": "apps", "gatewayBaseUrl": ra.STORAGE_GATEWAY_URL, "credentialRef": str(ra.STORAGE_CREDENTIAL), "verified": True},
        }
        ra.atomic_json(self.paths.runtime, self.profile, 0o600)
        marker = self.paths.deployments / "sample/release.json"
        marker.parent.mkdir()
        ra.atomic_json(marker, {"managedBy": ra.MANAGED_BY, "enterpriseKey": "aifabei", "storageMode": "oss-gateway", "storageEnvFile": str(self.secret)}, 0o600)
        self.old_env = b"OSS_BUCKET=source-files\nOSS_ENDPOINT=https://oss-cn-hongkong.aliyuncs.com\nOSS_ACCESS_KEY_ID=fixture\nOSS_ACCESS_KEY_SECRET=fixture\n"
        self.new_env = self.old_env.replace(b"source-files", b"target-files").replace(b"cn-hongkong", b"cn-hangzhou")
        ra.atomic_write(self.env, self.old_env, 0o600)
        with contextlib.closing(sqlite3.connect(self.registry)) as db:
            db.execute("CREATE TABLE identities (name TEXT PRIMARY KEY)")
            db.execute("INSERT INTO identities VALUES ('sample')")
            db.commit()
        self.registry.chmod(0o600)
        item = {"size": 3, "etag": "multipart-etag-2", "crc64": "1234567", "metadata": {"content-type": "text/plain"}}
        self.manifest = {
            "schemaVersion": 1, "operationId": "b" * 32,
            "capturedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
            "sourceWritesFrozen": True,
            "source": {"host": "8.218.208.205", "machineId": "1" * 32, "runtimeSha256": migration.sha(self.paths.runtime.read_bytes()), "bucket": "source-files", "region": "cn-hongkong", "versioning": "Disabled", "enumerationComplete": True, "objectCount": 1, "totalBytes": 3},
            "target": {"host": "47.97.90.161", "machineId": "2" * 32, "bucket": "target-files", "region": "cn-hangzhou", "versioning": "Disabled", "enumerationComplete": True, "objectCount": 1, "totalBytes": 3},
            "identity": {k: self.profile[k] for k in ("enterpriseKey", "organizationId", "runtimeId")},
            "releaseSha256": {"sample": migration.sha(marker.read_bytes())},
            "objects": [{"key": "apps/sample/example", "size": 3, "source": copy.deepcopy(item), "target": copy.deepcopy(item)}],
            "objectCount": 1, "totalBytes": 3, "stoppedUnits": sorted(migration.REQUIRED_UNITS),
        }
        self.host = FakeHost()

    def raw(self):
        return json.dumps(self.manifest).encode()

    def run_migration(self, **kwargs):
        return migration.migrate(self.raw(), self.new_env, self.paths, self.env, self.registry, self.host, **kwargs)

    def test_complete_crc_inventory_and_sha_fallback(self):
        migration.parse_manifest(self.raw())
        for side in ("source", "target"):
            self.manifest["objects"][0][side].pop("crc64")
            self.manifest["objects"][0][side]["sha256"] = "c" * 64
        migration.parse_manifest(self.raw())

    def test_rejects_incomplete_changed_or_etag_only_evidence(self):
        original = copy.deepcopy(self.manifest)
        cases = [
            lambda x: x["target"].update(enumerationComplete=False),
            lambda x: x["target"].update(objectCount=2),
            lambda x: x["target"].update(totalBytes=4),
            lambda x: x["source"].update(versioning="Enabled"),
            lambda x: x.update(sourceWritesFrozen=False),
            lambda x: x["target"].update(machineId=x["source"]["machineId"]),
            lambda x: x["objects"][0]["target"].update(size=4),
            lambda x: x["objects"][0]["target"].update(crc64="999"),
            lambda x: x["objects"][0]["target"].update(metadata={}),
            lambda x: x["objects"][0]["source"].pop("crc64"),
            lambda x: x["objects"].append(copy.deepcopy(x["objects"][0])),
            lambda x: x.update(capturedAt="2020-01-01T00:00:00Z"),
        ]
        for mutate in cases:
            with self.subTest(case=cases.index(mutate)):
                self.manifest = copy.deepcopy(original)
                mutate(self.manifest)
                with self.assertRaises(migration.MigrationError):
                    migration.parse_manifest(self.raw())

    def test_success_preserves_identity_releases_tokens_and_is_idempotent(self):
        token = self.secret.read_bytes()
        releases = {p: p.read_bytes() for p in self.paths.deployments.glob("*/release.json")}
        self.assertEqual(self.run_migration()["phase"], "committed")
        updated = json.loads(self.paths.runtime.read_bytes())
        self.assertEqual(updated["objectStorage"]["bucket"], "target-files")
        self.assertEqual(updated["objectStorage"]["region"], "cn-hangzhou")
        for key, value in self.manifest["identity"].items():
            self.assertEqual(updated[key], value)
        self.assertEqual(self.env.read_bytes(), self.new_env)
        self.assertEqual(self.secret.read_bytes(), token)
        self.assertEqual(releases, {p: p.read_bytes() for p in releases})
        self.assertFalse(self.run_migration()["changed"])
        self.assertEqual(self.host.calls.count("probe"), 1)

    def test_probe_failure_restores_profile_env_registry_and_keeps_business_stopped(self):
        original = self.paths.runtime.read_bytes()
        self.host.fail_probe = True
        with self.assertRaises(migration.MigrationError):
            self.run_migration()
        self.assertEqual(self.paths.runtime.read_bytes(), original)
        self.assertEqual(self.env.read_bytes(), self.old_env)
        with contextlib.closing(sqlite3.connect(self.registry)) as db:
            self.assertEqual(db.execute("SELECT name FROM identities").fetchall(), [("sample",)])
        self.assertEqual(self.run_migration()["phase"], "rolled-back")

    def test_changed_app_identity_is_restored(self):
        original = self.secret.read_bytes()
        self.host.during_probe = lambda: self.secret.write_bytes(b"unexpected-new-identity")
        with self.assertRaises(migration.MigrationError):
            self.run_migration()
        self.assertEqual(self.secret.read_bytes(), original)
        self.assertEqual(self.env.read_bytes(), self.old_env)

    def test_drift_or_active_business_refuses_before_any_stop(self):
        self.paths.runtime.write_bytes(self.paths.runtime.read_bytes() + b" ")
        with self.assertRaises(migration.MigrationError):
            self.run_migration()
        self.assertNotIn("stop", self.host.calls)
        self.host.business_running = True
        with self.assertRaises(migration.MigrationError):
            self.run_migration()
        self.assertNotIn("stop", self.host.calls)

    def test_explicit_rollback_after_commit_and_interrupted_commit_journal(self):
        original = self.paths.runtime.read_bytes()
        self.run_migration()
        state = self.paths.backups / "oss-scope" / self.manifest["operationId"] / "journal.json"
        journal = json.loads(state.read_bytes())
        # Simulates process loss after writing the new Runtime but before the
        # committed journal fsync. Retrying restores instead of guessing success.
        journal["phase"] = "prepared"
        ra.atomic_json(state, journal, 0o600)
        self.assertEqual(self.run_migration()["phase"], "rolled-back")
        self.assertEqual(self.paths.runtime.read_bytes(), original)
        self.assertEqual(self.env.read_bytes(), self.old_env)

    def test_committed_rollback_restores_and_rejects_manifest_reuse(self):
        original = self.paths.runtime.read_bytes()
        self.run_migration()
        raw = self.raw()
        self.manifest["target"]["host"] = "47.97.90.162"
        with self.assertRaises(migration.MigrationError):
            self.run_migration()
        self.manifest = json.loads(raw)
        self.assertEqual(self.run_migration(rollback=True)["phase"], "rolled-back")
        self.assertEqual(self.paths.runtime.read_bytes(), original)

    def test_real_host_fence_checks_machine_services_and_all_containers(self):
        host = migration.Host()
        def command(*args, **kwargs):
            return "inactive\n" if args[0] == "systemctl" else migration.GATEWAY + "\n"
        with mock.patch.object(Path, "read_text", return_value=self.manifest["target"]["machineId"]), mock.patch.object(host, "command", side_effect=command):
            host.fenced(self.manifest)
            with mock.patch.object(host, "command", return_value="active\n"):
                with self.assertRaises(migration.MigrationError):
                    host.fenced(self.manifest)
            with mock.patch.object(host, "command", side_effect=lambda *a, **k: "inactive\n" if a[0] == "systemctl" else "sample-app\n"):
                with self.assertRaises(migration.MigrationError):
                    host.fenced(self.manifest)
        with mock.patch.object(Path, "read_text", return_value=self.manifest["source"]["machineId"]):
            with self.assertRaises(migration.MigrationError):
                host.fenced(self.manifest)

    def test_gateway_recreation_pins_image_and_restores_private_networks(self):
        host = migration.Host()
        before = self.host.gateway_info()
        after = {**before, "networks": ["zhuojian-storage"]}
        commands = []
        def command(*args, **kwargs):
            commands.append(args)
            if args[:2] == ("docker", "compose"):
                files = [args[i + 1] for i, arg in enumerate(args) if arg == "-f"]
                config = json.loads(Path(files[1]).read_text())
                self.assertEqual(config["services"][migration.GATEWAY]["image"], before["image"])
                self.assertIn("--no-build", args)
                self.assertIn("never", args)
            return "healthy\n"
        with mock.patch.object(host, "command", side_effect=command), mock.patch.object(host, "gateway_info", return_value=after):
            host.recreate(before)
        self.assertIn(("docker", "network", "connect", "zhuojian-storage-sample", migration.GATEWAY), commands)

    def test_gateway_stop_tolerates_only_confirmed_container_absence(self):
        host = migration.Host()
        absent = subprocess.CompletedProcess([], 1, "[]\n", f"Error response from daemon: No such container: {migration.GATEWAY}\n")
        with mock.patch.object(subprocess, "run", return_value=absent) as command:
            host.stop()
            self.assertEqual(command.call_count, 1)
        for message in ("permission denied", "Cannot connect to the Docker daemon", "Error: No such container: some-other-container"):
            with mock.patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "", message)):
                with self.assertRaises(migration.MigrationError):
                    host.stop()

    def test_compose_failure_after_container_removal_restores_and_retry_is_safe(self):
        original = self.paths.runtime.read_bytes()
        count = 0
        def recreate(before):
            nonlocal count
            count += 1
            if count == 1:
                raise migration.MigrationError("replacement failed after deleting old container")
        with mock.patch.object(self.host, "recreate", side_effect=recreate):
            with self.assertRaises(migration.MigrationError):
                self.run_migration()
        self.assertEqual(count, 2)
        self.assertEqual(self.paths.runtime.read_bytes(), original)
        self.assertEqual(self.env.read_bytes(), self.old_env)
        self.assertEqual(self.run_migration()["phase"], "rolled-back")


if __name__ == "__main__":
    unittest.main()
