import copy
import contextlib
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import time
import threading
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import runtime_storage_bootstrap as bootstrap
import runtime_backup_oss as transport
import runtime_recovery_evidence as evidence
import runtime_online_backup as online
from scripts import publish_subsystem

HOST = Path(__file__).parents[1] / 'assets/admin-runtime/host'
SPEC = importlib.util.spec_from_file_location('test_bootstrap_plan', HOST / 'runtime_backup_plan.py')
plan = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plan)
ORG = '11111111-2222-4333-8444-555555555555'


def profile(tmp_path):
    config = tmp_path / 'etc'
    config.mkdir(mode=0o700)
    key = config / 'runtime.key'
    key.write_text('test-runtime-credential')
    key.chmod(0o600)
    return {'organizationId': ORG, 'runtimeId': 'runtime-one', 'enterpriseKey': 'test-company', 'environment': 'staging',
            'deployment': {'registrationCredentialRef': str(key), 'deploymentsRoot': str(tmp_path / 'releases'),
                           'backupsRoot': str(tmp_path / 'backups')},
            'platform': {'baseUrl': 'https://ai-platform.staging.zhuojianai.com'}}


def binding(p, *, business=False, applications=None):
    def scope(purpose):
        return {'bucket': 'shared-' + purpose, 'region': 'cn-hangzhou', 'endpoint': 'https://oss-cn-hangzhou-internal.aliyuncs.com',
                'rootPrefix': f"enterprises/{ORG}/staging/" + ('apps' if purpose == 'business' else 'backups')}
    return {'schemaVersion': 1, **bootstrap.identity(p), 'enabled': True, 'revision': 1,
            'credentialsEndpoint': bootstrap.API + 'storage-credentials', 'applicationSlugs': applications or [],
            'backup': scope('backup'), 'business': scope('business') if business else None,
            'backupPolicy': {'enabled': True, 'intervalHours': 24, 'localKeep': 2, 'automaticEnrollment': True}}


def lease(p, purpose, scope, *, expiration=None, key='test-key'):
    return {'schemaVersion': 1, **bootstrap.identity(p), 'revision': 1, 'purpose': purpose, **scope,
            'credentials': {'accessKeyId': key, 'accessKeySecret': 'test-secret', 'securityToken': 'test-sts',
                'expiresAt': expiration or (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=900)).isoformat()}}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps(value))
    path.chmod(0o600)


def test_binding_is_runtime_derived_and_business_can_stay_legacy(tmp_path):
    p = profile(tmp_path)
    value = binding(p)
    validated = bootstrap.validate_binding(p, value)
    assert validated['business'] is None
    assert validated['backup']['rootPrefix'] == f'enterprises/{ORG}/staging/backups'
    for key, change in [('organizationId', '66666666-2222-4333-8444-555555555555'), ('environment', 'production'),
                        ('runtimeId', 'other-runtime'), ('enabled', False)]:
        wrong = copy.deepcopy(value)
        wrong[key] = change
        with pytest.raises(transport.BackupError):
            bootstrap.validate_binding(p, wrong)
    for wrong in ['apps', f'enterprises/{ORG}/staging/backups/other', f'enterprises/{ORG}/staging/backups/']:
        value['backup']['rootPrefix'] = wrong
        with pytest.raises(transport.BackupError):
            bootstrap.validate_binding(p, value)


def test_lease_cannot_switch_purpose_scope_or_use_expired_credentials(tmp_path):
    p = profile(tmp_path)
    scope = binding(p)['backup']
    p['platformStorageBinding'] = bootstrap.validate_binding(p, binding(p))
    good = lease(p, 'backup', scope)
    assert bootstrap.validate_lease(p, 'backup', good, scope)['OSS_CREDENTIAL_PROVIDER'] == 'platform-sts-v1'
    for field, value in [('purpose', 'business'), ('bucket', 'other-bucket'), ('endpoint', 'https://example.com'),
                         ('rootPrefix', 'enterprises/other/staging/backups')]:
        wrong = copy.deepcopy(good)
        wrong[field] = value
        with pytest.raises(transport.BackupError):
            bootstrap.validate_lease(p, 'backup', wrong, scope)
    for delta in [-60, 30, 24 * 3600]:
        wrong = copy.deepcopy(good)
        wrong['credentials']['expiresAt'] = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=delta)).isoformat()
        with pytest.raises(transport.BackupError):
            bootstrap.validate_lease(p, 'backup', wrong, scope)


def test_request_signing_provider_renews_short_lease_and_preserves_scope(tmp_path):
    p = profile(tmp_path)
    p['platformStorageBinding'] = bootstrap.validate_binding(p, binding(p))
    path = tmp_path / 'etc' / 'backup.env'
    calls = []
    def broker(_p, route, body):
        calls.append((route, body))
        return lease(p, body['purpose'], p['platformStorageBinding'][body['purpose']], key='key-' + str(len(calls)))
    def refresh(_p, purpose, destination):
        return bootstrap.renew(_p, purpose, destination=destination, call=broker)
    provider = bootstrap.RuntimeCredentialsProvider(p, 'backup', path, refresher=refresh)
    assert provider.get_credentials().get_access_key_id() == 'key-1'
    assert provider.get_credentials().get_access_key_id() == 'key-1'
    values = bootstrap.credential_values(path)
    values['OSS_EXPIRES_AT'] = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=60)).isoformat()
    bootstrap.write_credentials(path, values)
    assert provider.get_credentials().get_access_key_id() == 'key-2'
    assert calls == [('storage-credentials', {'purpose': 'backup'})] * 2


def test_configure_preserves_legacy_business_and_requires_real_backup_boundary(tmp_path, monkeypatch):
    p = profile(tmp_path)
    p['objectStorage'] = {'provider': 'aliyun-oss', 'mode': 'gateway-api-v1', 'bucket': 'legacy-business', 'region': 'cn-hangzhou', 'rootPrefix': 'apps'}
    original_business = copy.deepcopy(p['objectStorage'])
    monkeypatch.setattr(bootstrap, 'PROFILE', tmp_path / 'etc' / 'runtime.json')
    monkeypatch.setattr(bootstrap, 'BACKUP_FILE', tmp_path / 'etc' / 'backup.env')
    purposes = []
    def call(_p, route, body=None):
        if route == 'storage-profile':
            return binding(p, business=True)
        purposes.append(body['purpose'])
        return lease(p, body['purpose'], binding(p)[body['purpose']])
    checks = []
    class Backend:
        def __init__(self, scope):
            assert scope.prefix.endswith('/staging/backups')
        def assert_scope(self, scope):
            checks.append('scope')
        def require_versioning(self):
            checks.append('versioning')
    monkeypatch.setattr(transport, 'OssBackend', Backend)
    configured, result = bootstrap.configure(p, call=call)
    assert configured['objectStorage'] == original_business
    assert configured['platformStorageBinding']['business'] is None
    assert purposes == ['backup']
    assert checks == ['scope', 'versioning']
    assert result['uploadVerified'] is False and result['recoveryVerified'] is False


def add_app(p, slug, tmp_path, *, database=True, url=None):
    data = tmp_path / 'data' / slug
    data.mkdir(parents=True)
    env = tmp_path / 'etc' / (slug + '.env')
    env.write_text('DATABASE_URL=' + (url or 'sqlite:////data/app.db') + '\n')
    env.chmod(0o600)
    if database:
        with sqlite3.connect(data / 'app.db') as db:
            db.execute('CREATE TABLE retained(id INTEGER PRIMARY KEY, value TEXT)')
            db.execute("INSERT INTO retained(value) VALUES ('original')")
            db.execute('CREATE TABLE stored_files(storage_key TEXT,storage_backend TEXT,deletion_state TEXT,size INTEGER,sha256 TEXT)')
    release = {'applicationSlug': slug, 'managedBy': 'zhuojian-runtime-admin/v1', 'dataDir': str(data), 'envFile': str(env),
               'current': {'commit': 'a' * 40}}
    write_json(Path(p['deployment']['deploymentsRoot']) / slug / 'release.json', release)
    return release


def test_enrollment_finds_actual_sqlite_preserves_reviewed_plan_and_flags_unknown(tmp_path):
    p = profile(tmp_path)
    release = add_app(p, 'records', tmp_path)
    add_app(p, 'external', tmp_path, database=False, url='postgresql://not-read-or-connected')
    path = tmp_path / 'etc' / 'plan.json'
    result = plan.enroll(p, plan_path=path, require_new=True)
    assert result['records']['primary_sqlite'] == '/data/app.db'
    assert result['external']['status'] == 'pending'
    assert result['external']['reason'] == 'database_adapter_required'
    with sqlite3.connect(Path(release['dataDir']) / 'app.db') as db:
        assert db.execute('SELECT value FROM retained').fetchone()[0] == 'original'
    saved = plan.read_json(path)
    saved['applications']['records']['known_missing_references'] = {'existing': 'preserve'}
    plan.atomic_json(path, saved)
    plan.enroll(p, plan_path=path, require_new=True)
    assert plan.read_json(path)['applications']['records'] == saved['applications']['records']


def test_unknown_sqlite_file_reference_schema_is_not_marked_protected(tmp_path):
    p = profile(tmp_path)
    release = add_app(p, 'custom-schema', tmp_path)
    with sqlite3.connect(Path(release['dataDir']) / 'app.db') as database:
        database.execute('DROP TABLE stored_files')
        database.execute('CREATE TABLE private_uploads(external_url TEXT)')
    result = plan.discover_database(release)
    assert result == {'status': 'pending', 'reason': 'file_reference_adapter_required', 'database_kind': 'sqlite'}


def test_explicit_sqlite_dsn_cannot_fall_back_to_an_unrelated_old_database(tmp_path):
    p = profile(tmp_path)
    release = add_app(p, 'declared', tmp_path, url='sqlite:////app/real-production.db')
    result = plan.discover_database(release)
    assert result['status'] == 'pending'
    assert result['reason'] == 'declared_sqlite_not_in_verified_mount'


def test_bad_one_app_discovery_does_not_abort_other_plan_enrollment(tmp_path):
    p = profile(tmp_path)
    bad = add_app(p, 'bad-config', tmp_path)
    Path(bad['envFile']).unlink()
    add_app(p, 'healthy', tmp_path)
    result = plan.enroll(p, plan_path=tmp_path / 'etc' / 'plan.json', require_new=True)
    assert result['bad-config'] == {'status': 'pending', 'reason': 'database_discovery_failed'}
    assert result['healthy']['status'] == 'ready'


def test_new_registration_requires_current_commit_cloud_and_isolated_proof(tmp_path):
    p = profile(tmp_path)
    p['platformStorageBinding'] = {'enabled': True}
    add_app(p, 'records', tmp_path)
    plan_path = tmp_path / 'etc' / 'backup-online-plan.json'
    plan.enroll(p, plan_path=plan_path, require_new=True)
    assert plan.protection_status(p, 'records', 'a' * 40, plan_path=plan_path)['status'] == 'pending_first_verified_point'
    archive = '20261028T000000.000000Z-' + 'a' * 12 + '.tar.gz'
    root = Path(p['deployment']['backupsRoot']) / 'records'
    sha = 'b' * 64
    write_json(root / (archive + '.json'), {'schemaVersion': 3, 'applicationSlug': 'records', 'commit': 'a' * 40, 'sha256': sha})
    write_json(root / (archive + '.remote.json'), {**bootstrap.identity(p), 'applicationSlug': 'records', 'archive': archive, 'sha256': sha,
                'offServer': True, 'fullReadbackAt': '2026-10-28T00:01:00Z', 'versionId': 'version-one'})
    restore = {'archiveName': archive, 'sha256': sha, 'versionId': 'version-one', 'businessDatabaseVerified': True,
               'fileHashesVerified': True, 'referenceIntegrityVerified': True, 'gitVerified': True, 'referencesRequeried': True}
    write_json(root / (archive + '.restore.json'), restore)
    assert plan.protection_status(p, 'records', 'a' * 40, plan_path=plan_path)['status'] == 'verified'
    assert plan.protection_status(p, 'records', 'c' * 40, plan_path=plan_path)['status'] != 'verified'
    restore['referenceIntegrityVerified'] = False
    write_json(root / (archive + '.restore.json'), restore)
    with pytest.raises(SystemExit, match='首次机外备份'):
        publish_subsystem.require_initial_backup(p, 'records', 'a' * 40, tmp_path / 'etc' / 'runtime.json')
    # Existing applications remain deployable even while a known partial point
    # is retained. Only new opt-in applications have the registration gate.
    saved = plan.read_json(plan_path)
    saved['applications']['records']['initialProtectionRequired'] = False
    plan.atomic_json(plan_path, saved)
    publish_subsystem.require_initial_backup(p, 'records', 'a' * 40, tmp_path / 'etc' / 'runtime.json')


def test_report_uses_authoritative_runtime_apps_and_keeps_pending_visible(tmp_path, monkeypatch):
    p = profile(tmp_path)
    cfg = binding(p, applications=['registered', 'missing-local'])
    p['backupStorage'] = cfg['backup']
    plan_path = tmp_path / 'etc' / 'plan.json'
    write_json(plan_path, {**bootstrap.identity(p), 'source_id': 'source-one', 'host_id': 'host-one',
        'applications': {'registered': {'name': 'Registered', 'primary_sqlite': '/data/app.db'},
                         'not-yet-registered': {'name': 'Local Candidate', 'primary_sqlite': '/data/app.db'}}})
    monkeypatch.setattr(bootstrap, 'PLAN', plan_path)
    monkeypatch.setattr(bootstrap, 'command', lambda *_a, **_k: SimpleNamespace(returncode=0))
    sent = []
    def call(_p, route, body=None):
        if route == 'storage-profile':
            return cfg
        sent.append(body)
        return {'ok': True}
    result = bootstrap.report(p, call=call)
    payload = sent[0]
    assert {row['applicationSlug'] for row in payload['systems']} == {'registered', 'missing-local'}
    assert payload['enrollment'] == {'registered': 2, 'covered': 1, 'pending': 1, 'failed': 0}
    assert payload['bindingRevision'] == 1
    assert result['pending'] == 1
    assert all(row['latestSuccessfulPoint'] is None for row in payload['systems'])
    assert 'credential' not in json.dumps(payload).lower()


def test_fixed_units_do_not_run_shell_or_share_registration_key():
    units = bootstrap.unit_contents(24)
    combined = '\n'.join(units.values())
    assert 'backup-all' not in combined
    assert '/bin/sh' not in combined and 'runtime-registration.key' not in combined
    assert 'CPUQuota=100%' in combined and 'MemoryMax=1536M' in combined
    assert 'serve-business' in units['zhuojian-business-lease.service']
    assert 'RuntimeDirectoryPreserve=yes' in units['zhuojian-business-lease.service']


def test_pending_or_new_unplanned_app_does_not_prevent_other_online_backup(tmp_path, monkeypatch, capsys):
    p = profile(tmp_path)
    for slug in ('known', 'pending', 'new-unplanned'):
        add_app(p, slug, tmp_path, database=(slug == 'known'))
    path = tmp_path / 'etc' / 'runtime.json'
    write_json(path, p)
    planned = tmp_path / 'etc' / 'online.json'
    write_json(planned, {**bootstrap.identity(p), 'applications': {
        'known': {'primary_sqlite': '/data/app.db'}, 'pending': {'enrollment': {'status': 'pending'}}}})
    monkeypatch.setattr(online, 'os', SimpleNamespace(name='posix', geteuid=lambda: 0))
    monkeypatch.setattr(transport, 'publication_lock', lambda _p: contextlib.nullcontext())
    monkeypatch.setattr(online, 'load_runtime_helper', lambda _p: object())
    captured = []
    def capture(_profile, slug, app, **_kwargs):
        captured.append(slug)
        return {'archive': str(tmp_path / (slug + '.tar.gz'))}
    monkeypatch.setattr(online, 'capture_one', capture)
    preserved = Path(p['deployment']['backupsRoot']) / 'known' / 'prior-valid-point'
    preserved.parent.mkdir(parents=True)
    preserved.write_bytes(b'keep original verified point')
    assert online.main(['--runtime-profile', str(path), '--plan', str(planned)]) == 2
    result = json.loads(capsys.readouterr().out)
    assert captured == ['known'] and len(result['backups']) == 1
    assert {row['applicationSlug'] for row in result['failed']} == {'pending', 'new-unplanned'}
    assert all(row['error_code'] == 'backup_plan_pending' for row in result['failed'])
    assert preserved.read_bytes() == b'keep original verified point'


def test_cloud_boundary_failure_restores_original_static_credential_bytes(tmp_path, monkeypatch):
    p = profile(tmp_path)
    backup_file = tmp_path / 'etc' / 'backup.env'
    original = b'# original private identity\nOSS_BUCKET=shared-backup\nOSS_ACCESS_KEY_ID="test-key"\nOSS_ACCESS_KEY_SECRET=\'test-secret\'\n'
    backup_file.write_bytes(original)
    backup_file.chmod(0o600)
    monkeypatch.setattr(bootstrap, 'BACKUP_FILE', backup_file)
    monkeypatch.setattr(bootstrap, 'PROFILE', tmp_path / 'etc' / 'runtime.json')
    def call(_p, route, body=None):
        if route == 'storage-profile':
            return binding(p)
        return lease(p, 'backup', binding(p)['backup'])
    class Backend:
        def __init__(self, _scope):
            pass
        def assert_scope(self, _scope):
            raise transport.BackupError('test boundary failed')
    monkeypatch.setattr(transport, 'OssBackend', Backend)
    with pytest.raises(transport.BackupError, match='boundary failed'):
        bootstrap.configure(p, call=call)
    assert backup_file.read_bytes() == original


def test_short_lease_can_renew_after_same_scope_binding_revision_changes(tmp_path):
    p = profile(tmp_path)
    p['platformStorageBinding'] = bootstrap.validate_binding(p, binding(p))
    cfg = binding(p)
    cfg['revision'] = 2
    def broker(_p, route, body=None):
        if route == 'storage-profile':
            return cfg
        response = lease(p, 'backup', cfg['backup'])
        response['revision'] = 2
        return response
    result = bootstrap.renew(p, 'backup', destination=tmp_path / 'etc' / 'lease.env', call=broker)
    assert result['OSS_PURPOSE'] == 'backup'
    assert result['OSS_ROOT_PREFIX'] == cfg['backup']['rootPrefix']


def test_successful_new_deploy_enrolls_and_queues_its_first_real_backup(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('storage_bootstrap_runtime_hook_test', HOST / 'runtime_admin.py')
    runtime = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = runtime
    spec.loader.exec_module(runtime)
    p = profile(tmp_path)
    p['platformStorageBinding'] = {'enabled': True}
    add_app(p, 'new-records', tmp_path)
    paths = SimpleNamespace(runtime=tmp_path / 'etc' / 'runtime.json')
    monkeypatch.setattr(runtime, 'locked', lambda _p: contextlib.nullcontext())
    calls = []
    def run(argv, **_kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(runtime, 'run', run)
    result = runtime.enroll_deployed_backup(p, 'new-records', 'a' * 40, paths)
    assert result['initialBackupQueued'] is True and result['required'] is True
    assert result['status'] == 'pending_first_verified_point'
    assert calls == [['systemctl', 'start', '--no-block', 'zhuojian-initial-backup@new-records.service']]
    saved = plan.read_json(tmp_path / 'etc' / 'backup-online-plan.json')
    assert saved['applications']['new-records']['initialProtectionRequired'] is True


def test_new_sts_upload_does_not_request_acl_modification():
    backend = transport.OssBackend.__new__(transport.OssBackend)
    backend.platform_sts = True
    calls = []
    class Bucket:
        def put_object(self, key, data, headers):
            calls.append(headers)
            return SimpleNamespace(headers={'x-oss-version-id': 'version-one'})
    backend.bucket = Bucket()
    assert backend.put_manifest('test-key', {'test': True}) == 'version-one'
    assert calls[0]['x-oss-server-side-encryption'] == 'AES256'
    assert 'x-oss-object-acl' not in calls[0]


@pytest.mark.parametrize('interrupt_after_replace', [False, True])
def test_configuration_cancellation_restores_all_original_bytes(tmp_path, monkeypatch, interrupt_after_replace):
    directory = tmp_path / 'private'
    directory.mkdir(mode=0o700)
    profile_path, backup_path, business_path = [directory / name for name in ('profile.json', 'backup.env', 'business.env')]
    profile_path.write_bytes(b'{"old":"profile"}')
    backup_path.write_bytes(b'# old static identity\nTEST=original\n')
    profile_path.chmod(0o600)
    backup_path.chmod(0o600)
    monkeypatch.setattr(bootstrap, 'PROFILE', profile_path)
    payloads = {profile_path: b'{"new":"profile"}', backup_path: b'NEW=lease\n', business_path: b'NEW=business\n'}
    original_write = bootstrap.atomic_private_bytes
    interrupted = False
    def write(path, payload, mode=0o600):
        nonlocal interrupted
        if path == business_path and not interrupted:
            interrupted = True
            if interrupt_after_replace:
                original_write(path, payload, mode)
            raise KeyboardInterrupt
        original_write(path, payload, mode)
    monkeypatch.setattr(bootstrap, 'atomic_private_bytes', write)
    with pytest.raises(KeyboardInterrupt):
        bootstrap.commit_configuration(payloads)
    assert profile_path.read_bytes() == b'{"old":"profile"}'
    assert backup_path.read_bytes() == b'# old static identity\nTEST=original\n'
    assert not business_path.exists()


@pytest.mark.skipif(os.name != 'posix' or getattr(os, 'geteuid', lambda: 1)() != 0, reason='real root flock queue')
def test_first_backup_waits_for_existing_runtime_work_without_stopping_it(tmp_path):
    path = tmp_path / 'runtime.lock'
    held = threading.Event()
    released = threading.Event()
    def holder():
        with transport.publication_lock(path):
            held.set()
            time.sleep(0.2)
        released.set()
    thread = threading.Thread(target=holder)
    thread.start()
    assert held.wait(2)
    try:
        with transport.publication_lock_wait(path, 2):
            assert released.is_set()
    finally:
        thread.join(3)


def test_lease_refresh_and_report_continue_while_backup_owns_runtime_lock(tmp_path, monkeypatch, capsys):
    p = profile(tmp_path)
    p['platformStorageBinding'] = bootstrap.validate_binding(p, binding(p))
    path = tmp_path / 'etc' / 'runtime.json'
    write_json(path, p)
    monkeypatch.setattr(bootstrap, 'PROFILE', path)
    monkeypatch.setattr(bootstrap, 'os', SimpleNamespace(name='posix', geteuid=lambda: 0))
    @contextlib.contextmanager
    def busy(_path):
        try:
            raise BlockingIOError('test lock held')
        except BlockingIOError as exc:
            raise transport.BackupError('another publisher is handling this recovery point') from exc
        yield
    monkeypatch.setattr(transport, 'publication_lock', busy)
    calls = []
    monkeypatch.setattr(bootstrap, 'renew', lambda _p, purpose: calls.append(purpose))
    monkeypatch.setattr(bootstrap, 'report', lambda _p: {'reported': True})
    assert bootstrap.main(['refresh']) == 0
    assert calls == ['backup']
    assert json.loads(capsys.readouterr().out)['report']['reported'] is True


@pytest.mark.skipif(os.name != 'posix' or getattr(os, 'geteuid', lambda: 1)() != 0, reason='root Unix peer and socket permissions')
def test_business_socket_accepts_only_fixed_business_request(tmp_path):
    p = profile(tmp_path)
    path = tmp_path / 'etc' / 'runtime.json'
    write_json(path, p)
    directory = tmp_path / 'socket'
    target = directory / 'credentials.sock'
    source = ("import sys;from pathlib import Path;sys.path.insert(0," + repr(str(SCRIPTS)) + ");"
              "import runtime_storage_bootstrap as b;b.PROFILE=Path(" + repr(str(path)) + ");"
              "b.SOCKET_DIRECTORY=Path(" + repr(str(directory)) + ");b.SOCKET_PATH=Path(" + repr(str(target)) + ");"
              "b.renew=lambda profile,purpose: {'purpose':purpose,'test':'fake-only'};b.serve_business()")
    process = subprocess.Popen([sys.executable, '-c', source], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 5
        while not target.exists() and time.monotonic() < deadline:
            assert process.poll() is None
            time.sleep(0.02)
        assert target.exists() and directory.stat().st_mode & 0o777 == 0o700 and target.stat().st_mode & 0o777 == 0o600
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(5)
            client.connect(str(target))
            client.sendall(b'GET\n')
            response = json.loads(client.recv(4096))
            assert response == {'ok': True, 'credentials': {'purpose': 'business', 'test': 'fake-only'}}
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(5)
            client.connect(str(target))
            client.sendall(b'{"purpose":"backup"}\n')
            assert client.recv(4096) == b''
    finally:
        process.terminate()
        process.communicate(timeout=5)
