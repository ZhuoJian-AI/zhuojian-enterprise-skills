"""Real Git/archives plus simulated Docker boundaries; never contacts a host."""
import argparse
import contextlib
import copy
import importlib.util
import json
import subprocess
import sys
import tarfile
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "multi_owner_runtime", ROOT / "assets/admin-runtime/host/runtime_admin.py"
)
h = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = h
SPEC.loader.exec_module(h)


def git(project, *arguments):
    return subprocess.check_output(["git", "-C", str(project), *arguments], text=True, stderr=subprocess.PIPE).strip()


def commit(project, text="approved"):
    (project / "app.txt").write_text(text)
    git(project, "add", "app.txt", "Dockerfile")
    git(project, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", text)
    return git(project, "rev-parse", "HEAD")


@pytest.fixture
def project(tmp_path):
    path = tmp_path / "project"
    path.mkdir()
    git(path, "init", "-q")
    (path / "Dockerfile").write_text("FROM scratch\nCOPY app.txt /app.txt\n")
    commit(path)
    return path


def test_frozen_context_ignores_concurrent_worktree_changes_and_excludes_git_and_untracked(project):
    selected = git(project, "rev-parse", "HEAD")
    (project / "app.txt").write_text("another owner changed this")
    (project / ".env").write_text("PRIVATE=must-not-build")
    with h.frozen_git_context(project, selected) as frozen:
        assert (frozen / "app.txt").read_text() == "approved"
        assert not (frozen / ".git").exists()
        assert not (frozen / ".env").exists()
        assert frozen != project
        retained = frozen
    assert not retained.exists()
    assert (project / ".env").read_text() == "PRIVATE=must-not-build"


def test_real_deploy_passes_frozen_bytes_to_docker_even_if_editor_changes_original(project, tmp_path):
    selected = git(project, "rev-parse", "HEAD")
    release = {"applicationSlug": "app", "containerName": "test-app", "nginxConfig": str(tmp_path / "nginx"), "port": 18000}
    actual = h.run
    observed = {}

    class StopAtBuild(Exception):
        pass

    def run(argv, **kwargs):
        if argv[:2] == ["docker", "build"]:
            (project / "app.txt").write_text("UNCOMMITTED OTHER OWNER")
            observed.update(content=(Path(argv[-1]) / "app.txt").read_text(), image=argv[argv.index("--tag") + 1])
            raise StopAtBuild()
        assert argv[0] == "git"
        return actual(argv, **kwargs)

    patches = {
        "locked": lambda _: contextlib.nullcontext(), "load_runtime": lambda _: {"enterpriseKey": "test"},
        "validated_network_attachments": lambda *args: [], "release_path": lambda *args: tmp_path / "absent",
        "disk_state": lambda _: {"uploadsAllowed": True}, "write_disk_state": lambda *args: None,
        "expected_names": lambda *args: {"projectDir": str(project), "hostname": "app.invalid"},
        "provision_release": lambda *args: release, "replace_nginx": lambda *args: None,
        "issue_certificate": lambda *args: None, "restore_nginx": lambda *args: None,
        "inspect_managed_release_container": lambda *args, **kwargs: None,
        "validated_recorded_release_identity": lambda *args, **kwargs: None, "run": run,
    }
    with contextlib.ExitStack() as stack:
        for name, value in patches.items():
            stack.enter_context(mock.patch.object(h, name, value))
        with pytest.raises(StopAtBuild):
            h.cmd_deploy(argparse.Namespace(application_slug="app", issue_certificate=True, email=None, health_timeout=10))
    assert observed == {"content": "approved", "image": f"zhuojian/test/app:{selected}"}


def test_late_candidate_and_changed_expected_current_are_rejected(project):
    first = git(project, "rev-parse", "HEAD")
    second = commit(project, "live second")
    h.assert_deploy_baseline(project, second, first, first)
    with pytest.raises(h.AdminError, match="current release changed"):
        h.assert_deploy_baseline(project, second, second, first)
    with pytest.raises(h.AdminError, match="candidate omits"):
        h.assert_deploy_baseline(project, first, second, None)
    with pytest.raises(h.AdminError, match="current release changed"):
        h.assert_deploy_baseline(project, second, second, "none")


def test_exact_worktree_commit_can_build_without_changing_shared_head(project, tmp_path):
    original = git(project, "rev-parse", "HEAD")
    task = tmp_path / "task"
    git(project, "worktree", "add", "-b", "task-one", str(task), original)
    target = commit(task, "task committed")
    (project / "app.txt").write_text("another task still editing")
    assert h.selected_git_commit(project, target) == target
    h.assert_deploy_baseline(project, target, original, original)
    with h.frozen_git_context(project, target) as frozen:
        assert (frozen / "app.txt").read_text() == "task committed"
    assert git(project, "rev-parse", "HEAD") == original


def test_explicit_commit_cannot_silently_use_a_parent_repository(project):
    nested = project / "nested"
    nested.mkdir()
    with pytest.raises(h.AdminError, match="root of its own"):
        h.selected_git_commit(nested, git(project, "rev-parse", "HEAD"))


def test_release_source_ref_survives_task_branch_removal_and_refuses_overwrite(project):
    base = git(project, "rev-parse", "HEAD")
    git(project, "checkout", "-b", "completed-task")
    deployed = commit(project, "deployed task")
    h.pin_release_commit(project, deployed)
    h.pin_release_commit(project, deployed)
    git(project, "checkout", "--detach", base)
    git(project, "branch", "-D", "completed-task")
    assert git(project, "rev-parse", f"refs/zhuojian/releases/{deployed}") == deployed
    git(project, "update-ref", f"refs/zhuojian/releases/{deployed}", base)
    with pytest.raises(h.AdminError, match="protected source ref differs"):
        h.pin_release_commit(project, deployed)


def test_bundle_contains_all_refs_and_running_commit_and_restores_without_original(project, tmp_path):
    running = git(project, "rev-parse", "HEAD")
    git(project, "branch", "running-release", running)
    later = commit(project, "later development")
    bundle = tmp_path / "repository.bundle"
    result = h.backup_git_repository(project, running, bundle)
    assert result["restoreVerified"] and result["workingTreeClean"]
    assert result["bundleSha256"] == h.sha256_file(bundle)
    clone = tmp_path / "independent"
    subprocess.run(["git", "clone", "--mirror", str(bundle), str(clone)], check=True, capture_output=True)
    assert git(clone, "rev-parse", "refs/heads/running-release") == running
    assert git(clone, "rev-parse", "HEAD") == later
    assert git(clone, "show", f"{running}:app.txt") == "approved"


def test_bundle_does_not_claim_uncommitted_work_is_preserved(project, tmp_path):
    running = git(project, "rev-parse", "HEAD")
    (project / "app.txt").write_text("not committed")
    result = h.backup_git_repository(project, running, tmp_path / "repository.bundle")
    assert not result["workingTreeClean"]
    assert result["uncommittedStateIncluded"] is False


def test_bundle_preserves_running_commit_even_when_no_branch_points_to_it(project, tmp_path):
    base = git(project, "rev-parse", "HEAD")
    git(project, "checkout", "--detach", base)
    orphan = commit(project, "running from completed task")
    git(project, "checkout", "--detach", base)
    result = h.backup_git_repository(project, orphan, tmp_path / "repository.bundle")
    assert result["requiredReleaseCommit"] == orphan and result["restoreVerified"]


@pytest.fixture
def release_fixture(project, tmp_path):
    paths = h.Paths(repositories=tmp_path, deployments=tmp_path / "deployments", data=tmp_path / "data",
                    backups=tmp_path / "backups", nginx=tmp_path / "nginx", apps_env=tmp_path / "apps")
    current = git(project, "rev-parse", "HEAD")
    for directory in (paths.deployments / "app", paths.data / "app", paths.nginx, paths.apps_env):
        directory.mkdir(parents=True)
    env = paths.apps_env / "app.env"
    env.write_text("PRIVATE=archived-only")
    nginx = paths.nginx / "app.conf"
    nginx.write_bytes(b"original nginx")
    (paths.data / "app" / "records.txt").write_text("business records")
    release = {"managedBy": h.MANAGED_BY, "applicationSlug": "app", "containerName": "test-app",
               "projectDir": str(project), "dataDir": str(paths.data / "app"), "envFile": str(env),
               "nginxConfig": str(nginx), "port": 18000, "hostname": "app.invalid",
               "current": {"commit": current, "image": f"zhuojian/test/app:{current}"}}
    h.atomic_json(h.release_path("app", paths), release)
    return paths, release


def test_pre_switch_backup_verifies_data_source_and_clean_recovery_config(release_fixture):
    paths, release = release_fixture
    release["releaseSwitch"] = {"previousNginx": h.encode_nginx_snapshot(b"original nginx")}
    Path(release["nginxConfig"]).write_bytes(b"maintenance nginx")
    with mock.patch.object(h, "container_running", return_value=False), mock.patch.object(h, "container_exists", return_value=False):
        result = h.backup_one("app", {"enterpriseKey": "test"}, paths, stopped_release=release)
    metadata = json.loads(Path(result["manifest"]).read_text())
    assert metadata["schemaVersion"] == 2 and metadata["offServer"] is False
    assert metadata["source"]["restoreVerified"]
    archive = Path(result["archive"])
    assert result["sha256"] == h.sha256_file(archive)
    assert result["sizeBytes"] == archive.stat().st_size
    with tarfile.open(archive) as bundle:
        assert bundle.extractfile("data/records.txt").read() == b"business records"
        assert bundle.extractfile("config/nginx.conf").read() == b"original nginx"
        saved = json.load(bundle.extractfile("config/release.json"))
        assert "releaseSwitch" not in saved
        assert bundle.extractfile("code/repository.bundle") is not None
    restored = paths.data / "restored"
    restored.mkdir()
    assert (h.safe_extract_data(archive, restored) / "records.txt").read_text() == "business records"
    assert not (restored / "code").exists()


def test_backup_recovery_restarts_then_checks_health_before_reopening(release_fixture):
    paths, release = release_fixture
    release["backupMaintenance"] = {**release["current"], "wasRunning": True,
                                    "previousNginx": h.encode_nginx_snapshot(b"original nginx")}
    calls = []
    actual = {"name": "test-app", "running": False, **release["current"]}
    with mock.patch.object(h, "inspect_managed_release_container", return_value=actual), \
         mock.patch.object(h, "run", side_effect=lambda argv: calls.append(argv)), \
         mock.patch.object(h, "wait_for_health", side_effect=lambda *args: calls.append("health")), \
         mock.patch.object(h, "restore_nginx", side_effect=lambda *args: calls.append("reopen")):
        recovered = h.recover_pending_backup(release, {"enterpriseKey": "test"}, paths)
    assert calls == [["docker", "start", "test-app"], "health", "reopen"]
    assert "backupMaintenance" not in recovered


def test_failed_backup_recovery_preserves_marker_and_maintenance(release_fixture):
    paths, release = release_fixture
    release["backupMaintenance"] = {**release["current"], "wasRunning": True,
                                    "previousNginx": h.encode_nginx_snapshot(b"original nginx")}
    h.atomic_json(h.release_path("app", paths), release)
    actual = {"name": "test-app", "running": True, **release["current"]}
    with mock.patch.object(h, "inspect_managed_release_container", return_value=actual), \
         mock.patch.object(h, "wait_for_health", side_effect=h.AdminError("unhealthy")), \
         mock.patch.object(h, "restore_nginx") as reopen:
        with pytest.raises(h.AdminError, match="unhealthy"):
            h.recover_pending_backup(release, {"enterpriseKey": "test"}, paths)
    reopen.assert_not_called()
    assert "backupMaintenance" in json.loads(h.release_path("app", paths).read_text())


def test_scheduled_backup_archive_failure_restores_old_service_and_keeps_existing_backups(release_fixture):
    paths, release = release_fixture
    existing = paths.backups / "app" / "previous.tar.gz"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"previous backup must survive")
    calls = []
    actual = {"name": "test-app", "running": False, **release["current"]}
    with contextlib.ExitStack() as stack:
        patches = {
            "load_release": mock.Mock(return_value=release),
            "container_running": mock.Mock(return_value=True),
            "container_exists": mock.Mock(return_value=True),
            "assert_managed_container": mock.Mock(),
            "maintenance_nginx_text": mock.Mock(return_value=b"maintenance"),
            "replace_nginx": mock.Mock(side_effect=lambda *args: calls.append("maintenance")),
            "run": None,
            "inspect_managed_release_container": mock.Mock(return_value=actual),
            "wait_for_health": mock.Mock(side_effect=lambda *args: calls.append("health")),
            "restore_nginx": mock.Mock(side_effect=lambda *args: calls.append("reopen")),
            "verify_backup_archive": mock.Mock(side_effect=h.AdminError("archive readback failed")),
        }
        real_run = h.run
        patches["run"] = mock.Mock(side_effect=lambda argv, **kw: calls.append(argv[1]) if argv[0] == "docker" else real_run(argv, **kw))
        for name, value in patches.items():
            stack.enter_context(mock.patch.object(h, name, value))
        with pytest.raises(h.AdminError, match="archive readback failed"):
            h.backup_one("app", {"enterpriseKey": "test"}, paths)
    assert calls == ["maintenance", "stop", "start", "health", "reopen"]
    assert "backupMaintenance" not in json.loads(h.release_path("app", paths).read_text())
    assert list(existing.parent.iterdir()) == [existing]
    assert existing.read_bytes() == b"previous backup must survive"


@pytest.mark.parametrize("failure", [None, "backup", "candidate-health"])
def test_deploy_maintenance_backup_switch_and_failure_recovery_use_real_durable_records(release_fixture, failure):
    paths, release = release_fixture
    profile = {"enterpriseKey": "test"}
    project = Path(release["projectDir"])
    target = commit(project, "candidate")
    canonical = release["containerName"]
    containers = {canonical: {"name": canonical, "running": True, **release["current"]}}
    calls = []
    real_run = h.run

    def run(argv, **kwargs):
        if argv[0] != "docker":
            return real_run(argv, **kwargs)
        action = argv[1]
        calls.append(action)
        if action == "stop":
            containers[argv[-1]]["running"] = False
        elif action == "rename":
            containers[argv[-1]] = containers.pop(argv[-2])
            containers[argv[-1]]["name"] = argv[-1]
        elif action == "start":
            containers[argv[-1]]["running"] = True
        elif action == "rm":
            containers.pop(argv[-1])
        return mock.Mock(returncode=0, stdout="", stderr="")

    def replace(path, payload):
        old = path.read_bytes()
        calls.append("maintenance" if b"SUBSYSTEM_MAINTENANCE" in payload else "reopen")
        path.write_bytes(payload)
        return old

    def start(name, image, *args):
        calls.append("candidate-start")
        containers[name] = {"name": name, "running": True, "image": image, "commit": target}

    def health(*args, **kwargs):
        current = containers[canonical]["commit"]
        calls.append("candidate-health" if current == target else "old-health")
        if failure == "candidate-health" and current == target:
            raise h.AdminError("candidate is unhealthy")

    actual_verify = h.verify_backup_archive

    def verify(archive):
        calls.append("backup-readback")
        if failure == "backup":
            raise h.AdminError("backup readback failed")
        actual_verify(archive)

    patches = {
        "locked": lambda _: contextlib.nullcontext(), "load_runtime": lambda _: profile,
        "load_release": lambda slug, *args: json.loads(h.release_path(slug, paths).read_text()),
        "validated_network_attachments": lambda *args: [],
        "disk_state": lambda _: {"uploadsAllowed": True}, "write_disk_state": lambda *args: None,
        "expected_names": lambda *args: release, "provision_release": lambda *args: copy.deepcopy(release),
        "issue_certificate": lambda *args: None, "replace_nginx": replace, "restore_nginx": replace,
        "inspect_managed_release_container": lambda name, *args, **kw: copy.deepcopy(containers.get(name)),
        "container_exists": lambda name: name in containers,
        "container_running": lambda name: containers.get(name, {}).get("running", False),
        "assert_managed_container": lambda *args: None, "run": run,
        "start_container": start, "wait_for_health": health, "verify_backup_archive": verify,
        "nginx_text": lambda *args: "server {\n    ssl_protocols TLSv1.2 TLSv1.3;\n}",
        "begin_platform_release_change": lambda *args: True,
        "reconcile_platform_release_change": lambda *args: calls.append("platform-reconciled"),
    }
    args = argparse.Namespace(application_slug="app", source_commit=target, expected_current_commit=release["current"]["commit"],
                              issue_certificate=True, email=None, health_timeout=10)
    with contextlib.ExitStack() as stack:
        for name, value in patches.items():
            stack.enter_context(mock.patch.object(h, name, value))
        if failure:
            with pytest.raises(h.AdminError, match="backup readback failed|candidate is unhealthy"):
                h.cmd_deploy(args, paths)
        else:
            result = h.cmd_deploy(args, paths)
            assert result["deploymentMode"] == "controlled-maintenance"
            assert Path(result["safetyBackup"]["manifest"]).is_file()
    saved = json.loads(h.release_path("app", paths).read_text())
    assert "releaseSwitch" not in saved and "backupMaintenance" not in saved
    assert calls.index("build") < calls.index("maintenance") < calls.index("stop") < calls.index("backup-readback")
    if failure:
        assert saved["current"]["commit"] == release["current"]["commit"]
        assert containers[canonical]["commit"] == release["current"]["commit"]
        assert calls[-3:] == ["old-health", "reopen", "platform-reconciled"]
        if failure == "backup":
            assert "candidate-start" not in calls
    else:
        assert saved["current"]["commit"] == target
        assert calls.index("backup-readback") < calls.index("candidate-start") < calls.index("candidate-health")
        assert calls.index("candidate-health") < max(index for index, call in enumerate(calls) if call == "reopen")


def test_shared_oss_prefix_is_derived_from_runtime_identity():
    profile = {"organizationId": "10000000-0000-4000-8000-000000000001", "environment": "staging"}
    assert h.storage_root_prefix(profile, "enterprise-v1") == "enterprises/10000000-0000-4000-8000-000000000001/staging/apps"
    assert h.storage_root_prefix({}, "legacy-apps") == "apps"
    with pytest.raises(h.AdminError):
        h.storage_root_prefix({**profile, "organizationId": "alphabet/another"}, "enterprise-v1")


def test_gateway_probe_checks_exact_namespace_and_never_relays_untrusted_output():
    prefix = "enterprises/10000000-0000-4000-8000-000000000001/staging/apps"
    required = ("anonymousReadDenied", "put", "get", "delete", "twoApplicationIsolation",
                "temporaryCredentialsRevoked", "outsidePrefixDenied")
    payload = {"ok": True, "rootPrefix": prefix, "checks": {key: True for key in required}}
    with mock.patch.object(h.subprocess, "run", return_value=mock.Mock(returncode=0, stdout=json.dumps(payload))) as probe:
        h.verify_storage_foundation("company-files", "oss-cn-hangzhou", prefix)
        assert probe.call_args.args[0][-2:] == ["--expected-root-prefix", prefix]
    payload["rootPrefix"] = "apps"
    payload["unexpectedSecret"] = "must-not-leak"
    with mock.patch.object(h.subprocess, "run", return_value=mock.Mock(returncode=0, stdout=json.dumps(payload))):
        with pytest.raises(h.AdminError, match="namespace differs") as caught:
            h.verify_storage_foundation("company-files", "oss-cn-hangzhou", prefix)
        assert "must-not-leak" not in str(caught.value)


def test_maintenance_gate_is_structured_and_cannot_silently_fail_open():
    with mock.patch.object(h, "nginx_text", return_value="server {\n    ssl_protocols TLSv1.2 TLSv1.3;\n}"):
        config = h.maintenance_nginx_text("app", {"port": 18000}, {})
    assert b'default_type application/json;' in config
    assert b'add_header Retry-After 30 always;' in config
    assert b'return 503 \'{"code":"SUBSYSTEM_MAINTENANCE"}\';' in config
    with mock.patch.object(h, "nginx_text", return_value="unexpected config format"):
        with pytest.raises(h.AdminError, match="maintenance gate"):
            h.maintenance_nginx_text("app", {"port": 18000}, {})


def test_cli_accepts_machine_managed_source_and_baseline_without_new_human_approval():
    args = h.parser().parse_args(["deploy", "orders", "--source-commit", "a" * 40, "--expected-current-commit", "b" * 40])
    assert args.source_commit == "a" * 40 and args.expected_current_commit == "b" * 40
