import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / 'scripts/maintenance'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('alphabet_storage_preflight_upgrade', SCRIPTS / 'upgrade_alphabet_storage_bootstrap_20261028.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def plan_and_baseline():
    plan = {'organizationId': module.original.ORG, 'runtimeId': 'aifabei-hk-01', 'environment': 'staging',
            'source_id': 'existing-source', 'applications': {'existing': {'primary_sqlite': '/data/original.db',
            'known_missing_references': {'file': 'original-baseline'}, 'private_host_files': {'original': '/etc/owned'}}}}
    baseline = {'identitySha256': sha({k: v for k, v in plan.items() if k != 'applications'}),
                'applications': {k: sha(v) for k, v in plan['applications'].items()}}
    return plan, baseline


def new_app(status='ready'):
    app = {'name': 'new-system', 'project_id': None, 'initialProtectionRequired': True,
           'enrollment': {'managedBy': 'zhuojian-runtime-backup-enrollment/v1', 'status': status,
                          'observedCommit': 'a' * 40}}
    if status == 'ready':
        app['primary_sqlite'] = '/data/app.sqlite3'
        app['enrollment'].update(primary_sqlite=app['primary_sqlite'], database_kind='sqlite', method='sqlite_magic_and_runtime_mount')
    else:
        app['enrollment']['reason'] = 'database_adapter_required'
    return app


@pytest.mark.parametrize('status', ['ready', 'pending'])
def test_existing_manual_plan_and_new_ready_or_pending_system_can_coexist(status):
    plan, baseline = plan_and_baseline()
    before = copy.deepcopy(plan['applications']['existing'])
    plan['applications']['new-system'] = new_app(status)
    for raw in (json.dumps(plan), json.dumps(plan, separators=(',', ':')), json.dumps(plan, indent=4)):
        module.validate_plan(json.loads(raw), baseline)
    assert plan['applications']['existing'] == before


@pytest.mark.parametrize('change', ['old-item', 'missing-item', 'identity', 'unowned', 'host-files', 'outside', 'traversal', 'mixed-path', 'unsupported-ready'])
def test_reviewed_baseline_and_enrollment_boundary_reject_unreviewed_changes(change):
    plan, baseline = plan_and_baseline()
    app = new_app()
    plan['applications']['new-system'] = app
    if change == 'old-item': plan['applications']['existing']['known_missing_references'] = {}
    elif change == 'missing-item': del plan['applications']['existing']
    elif change == 'identity': plan['organizationId'] = 'another-organization'
    elif change == 'unowned': app['enrollment']['managedBy'] = 'caller'
    elif change == 'host-files': app['private_host_files'] = {'arbitrary': '/etc/another-file'}
    elif change == 'outside': app['primary_sqlite'] = '/etc/database.db'
    elif change == 'traversal': app['primary_sqlite'] = '/data/../private/db.sqlite'
    elif change == 'mixed-path': app['enrollment']['primary_sqlite'] = '/data/other.db'
    elif change == 'unsupported-ready': app['enrollment']['database_kind'] = 'postgres'
    with pytest.raises(ValueError): module.validate_plan(plan, baseline)


def generation_fixture():
    content = {'/usr/local/sbin/legacy': b'old-wrapper', '/legacy/module.py': b'old-module',
               '/usr/local/sbin/current': b'new-wrapper', '/current/module.py': b'renewable-module'}
    generations = {'legacy-static': {'wrappers': {'legacy': hashlib.sha256(content['/usr/local/sbin/legacy']).hexdigest()},
                                    'modules': {'/legacy/module.py': hashlib.sha256(content['/legacy/module.py']).hexdigest()}},
                   'platform-sts-v1': {'wrappers': {'current': hashlib.sha256(content['/usr/local/sbin/current']).hexdigest()},
                                       'modules': {'/current/module.py': hashlib.sha256(content['/current/module.py']).hexdigest()}}}
    def reader(path, *, private=False):
        key = path.as_posix()
        assert private is key.endswith('module.py')
        if key not in content: raise FileNotFoundError
        return content[key]
    return content, {'generations': generations}, reader


def test_legacy_static_schedule_keeps_working_but_cannot_use_sts():
    content, pins, reader = generation_fixture()
    del content['/usr/local/sbin/current']
    assert module.verify_generation(pins, {}, reader) == 'legacy-static'
    with pytest.raises(ValueError, match='renewable SDK'):
        module.verify_generation(pins, {'backupStorage': {'credentialProvider': 'platform-sts-v1'}}, reader)


def test_new_generation_requires_every_reviewed_wrapper_and_module():
    content, pins, reader = generation_fixture()
    del content['/usr/local/sbin/legacy']
    assert module.verify_generation(pins, {'backupStorage': {'credentialProvider': 'platform-sts-v1'}}, reader) == 'platform-sts-v1'
    content['/current/module.py'] = b'wrong-module'
    with pytest.raises(ValueError, match='unreviewed or mixed'):
        module.verify_generation(pins, {}, reader)


def test_generated_preflight_retains_original_windows_capacity_and_is_standalone():
    assert hashlib.sha256(module.original.PREFLIGHT.encode()).hexdigest() == module.OLD_PREFLIGHT_SHA
    rendered = module.render_preflight()
    compile(rendered, '<actual-rendered-preflight>', 'exec')
    original_windows = module.original.PREFLIGHT.split("if len(sys.argv)>1 and sys.argv[1]=='windows':", 1)[1]
    assert rendered.decode().endswith(original_windows)
    assert len(module.PLAN_BASELINE['applications']) == 9


@pytest.mark.parametrize('after_rename', [False, True])
def test_interrupted_preflight_commit_restores_original_bytes_and_modes(tmp_path, monkeypatch, after_rename):
    pins, preflight = tmp_path / 'pins.json', tmp_path / 'preflight.py'
    pins.write_bytes(b'old-pins'); preflight.write_bytes(b'old-preflight')
    original = {pins: b'old-pins', preflight: b'old-preflight'}
    before_modes = {p: stat.S_IMODE(p.stat().st_mode) for p in original}
    monkeypatch.setattr(module, 'regular', lambda path, **_kwargs: path.read_bytes())
    real_atomic = module.atomic
    interrupted = False
    def atomic(path, raw, mode):
        nonlocal interrupted
        # This maintenance entry only runs on GNU/Linux. Windows exercises the
        # transaction without pretending its read-only flag is a POSIX mode.
        if os.name == 'nt':
            path.chmod(0o600)
            mode = 0o600
        if path == preflight and raw == b'new-preflight' and not interrupted:
            interrupted = True
            if after_rename: real_atomic(path, raw, mode)
            raise KeyboardInterrupt
        real_atomic(path, raw, mode)
    monkeypatch.setattr(module, 'atomic', atomic)
    with pytest.raises(KeyboardInterrupt):
        module.commit_files({pins: (b'new-pins', 0o600), preflight: (b'new-preflight', 0o500)})
    assert all(path.read_bytes() == raw for path, raw in original.items())
    if os.name == 'posix':
        assert all(stat.S_IMODE(path.stat().st_mode) == mode for path, mode in before_modes.items())


def test_rollback_preserves_concurrent_unknown_write_and_restores_other_owned_file(tmp_path, monkeypatch):
    pins, preflight = tmp_path / 'pins.json', tmp_path / 'preflight.py'
    pins.write_bytes(b'old-pins'); preflight.write_bytes(b'old-preflight')
    monkeypatch.setattr(module, 'regular', lambda path, **_kwargs: path.read_bytes())
    real_atomic = module.atomic
    def writer(path, raw, mode):
        real_atomic(path, raw, 0o600)
        if path == preflight and raw == b'new-preflight':
            pins.write_bytes(b'concurrent-unknown')
            raise KeyboardInterrupt
    monkeypatch.setattr(module, 'atomic', writer)
    with pytest.raises(RuntimeError, match='rollback conflict'):
        module.commit_files({pins: (b'new-pins', 0o600), preflight: (b'new-preflight', 0o500)})
    assert pins.read_bytes() == b'concurrent-unknown'
    assert preflight.read_bytes() == b'old-preflight'


@pytest.mark.skipif(os.name != 'posix' or getattr(os, 'geteuid', lambda: 1)() != 0, reason='real root private-file preflight')
def test_rendered_preflight_runs_real_private_files_and_rejects_old_sts_pairing(tmp_path):
    plan, baseline = plan_and_baseline()
    plan['applications']['new-system'] = new_app('pending')
    wrappers = tmp_path / 'wrappers'
    wrappers.mkdir(mode=0o700)
    cli = wrappers / 'legacy'
    sdk = tmp_path / 'sdk.py'
    cli.write_bytes(b'old-cli'); cli.chmod(0o750)
    sdk.write_bytes(b'old-sdk'); sdk.chmod(0o600)
    pins = {'planBaseline': baseline, 'generations': {'legacy-static': {
        'wrappers': {'legacy': hashlib.sha256(cli.read_bytes()).hexdigest()},
        'modules': {str(sdk): hashlib.sha256(sdk.read_bytes()).hexdigest()},
    }}}
    profile = {k: plan[k] for k in ['organizationId', 'runtimeId', 'environment']}
    files = {'pins.json': pins, 'plan.json': plan, 'profile.json': profile}
    for name, value in files.items():
        target = tmp_path / name
        target.write_text(json.dumps(value)); target.chmod(0o600)
    machine = tmp_path / 'machine-id'
    machine.write_text(module.MACHINE)
    source = module.render_preflight().decode()
    source = source.replace("Path('/usr/local/sbin')", f'Path({str(wrappers)!r})')
    source = source.replace("Path('/etc/machine-id')", f'Path({str(machine)!r})')
    source = source.replace("Path('/etc/zhuojian/runtime.json')", f"Path({str(tmp_path / 'profile.json')!r})")
    source = source.replace("Path('/etc/zhuojian/backup-online-plan.json')", f"Path({str(tmp_path / 'plan.json')!r})")
    source = source.replace("shutil.disk_usage('/srv/zhuojian')", f'shutil.disk_usage({str(tmp_path)!r})')
    target = tmp_path / 'preflight.py'
    target.write_text(source); target.chmod(0o500)
    run = lambda: subprocess.run([sys.executable, str(target)], capture_output=True, timeout=10)
    assert run().returncode == 0
    profile['backupStorage'] = {'credentialProvider': 'platform-sts-v1'}
    (tmp_path / 'profile.json').write_text(json.dumps(profile))
    failure = run()
    assert failure.returncode != 0 and b'STS requires the renewable SDK generation' in failure.stderr
    profile.pop('backupStorage')
    (tmp_path / 'profile.json').write_text(json.dumps(profile))
    plan['applications']['existing']['primary_sqlite'] = '/data/wrong.db'
    (tmp_path / 'plan.json').write_text(json.dumps(plan))
    failure = run()
    assert failure.returncode != 0 and b'reviewed application plan changed' in failure.stderr
