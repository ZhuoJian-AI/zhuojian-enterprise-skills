#!/usr/bin/env python3
"""Use the existing Runtime identity to bind and renew scoped platform storage."""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import re
import socket
import socketserver
import stat
import struct
import subprocess
import tempfile
from urllib import error, request
from urllib.parse import urlsplit
from uuid import UUID

import runtime_backup_oss as transport

MARKER = 'zhuojian-runtime-storage-bootstrap/v1'
PROFILE = Path('/etc/zhuojian/runtime.json')
PLAN = Path('/etc/zhuojian/backup-online-plan.json')
BUSINESS_FILE = Path('/etc/zhuojian/oss-business-lease/credentials.env')
BACKUP_FILE = Path('/etc/zhuojian/backup-oss.env')
SOCKET_DIRECTORY = Path('/run/zhuojian-oss-lease/business')
SOCKET_PATH = SOCKET_DIRECTORY / 'credentials.sock'
API = '/api/v1/ecs-publisher/runtime/'
REFRESH_MARGIN = 120
MAX_RESPONSE = 512 * 1024
UTC = dt.timezone.utc


def parse_time(value):
    if not isinstance(value, str):
        raise transport.BackupError('storage lease expiration is missing')
    try:
        stamp = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise transport.BackupError('storage lease expiration is invalid') from exc
    if stamp.tzinfo is None:
        raise transport.BackupError('storage lease expiration must include timezone')
    return stamp.astimezone(UTC)


def identity(profile):
    try:
        organization = str(UUID(str(profile['organizationId'])))
    except (KeyError, ValueError, TypeError) as exc:
        raise transport.BackupError('Runtime storage identity is invalid') from exc
    environment = profile.get('environment')
    runtime = profile.get('runtimeId')
    enterprise = profile.get('enterpriseKey')
    if environment not in {'development', 'staging', 'production'} or not all(isinstance(v, str) and v for v in (runtime, enterprise)):
        raise transport.BackupError('Runtime storage identity is incomplete')
    return {'organizationId': organization, 'environment': environment, 'runtimeId': runtime, 'enterpriseKey': enterprise}


def validate_scope(profile, value, purpose):
    if purpose not in {'business', 'backup'} or not isinstance(value, dict):
        raise transport.BackupError('storage purpose is invalid')
    own = identity(profile)
    region = value.get('region')
    bucket = value.get('bucket')
    endpoint = value.get('endpoint')
    expected = f"enterprises/{own['organizationId']}/{own['environment']}/" + ('apps' if purpose == 'business' else 'backups')
    if not isinstance(region, str) or not re.fullmatch(r'[a-z][a-z0-9-]{1,47}', region):
        raise transport.BackupError('storage region is invalid')
    if not isinstance(bucket, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,61}[a-z0-9]', bucket):
        raise transport.BackupError('storage bucket is invalid')
    if endpoint not in {f'https://oss-{region}.aliyuncs.com', f'https://oss-{region}-internal.aliyuncs.com'} or value.get('rootPrefix') != expected:
        raise transport.BackupError('storage scope does not match this Runtime')
    return {k: value[k] for k in ('bucket', 'region', 'endpoint', 'rootPrefix')}


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        raise transport.BackupError('platform storage redirects are not allowed')


def platform_call(profile, route, payload=None):
    origin = profile.get('platform', {}).get('baseUrl', '')
    parsed = urlsplit(origin)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {'', '/'}:
        raise transport.BackupError('trusted Runtime platform origin is invalid')
    credential_path = Path(profile.get('deployment', {}).get('registrationCredentialRef', '/etc/zhuojian/runtime-registration.key'))
    transport.private_file(credential_path)
    token = credential_path.read_text(encoding='utf-8').strip()
    if not token or any(c in token for c in '\r\n'):
        raise transport.BackupError('Runtime machine credential is invalid')
    if route not in {'storage-profile', 'storage-credentials', 'storage-report'}:
        raise transport.BackupError('storage route is invalid')
    body = None if payload is None else json.dumps(payload, separators=(',', ':')).encode()
    req = request.Request(origin.rstrip('/') + API + route, data=body,
                          headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json', 'Content-Type': 'application/json'})
    try:
        # Environment proxy policy remains command-scoped; credentials never
        # follow a cross-origin redirect and never appear in error output.
        with request.build_opener(NoRedirect()).open(req, timeout=30) as response:
            raw = response.read(MAX_RESPONSE + 1)
    except error.HTTPError as exc:
        code = {403: 'storage_disabled', 409: 'storage_not_provisioned', 503: 'storage_credentials_unavailable'}.get(exc.code, 'storage_platform_request_failed')
        raise transport.BackupError(code) from None
    except (error.URLError, OSError):
        raise transport.BackupError('storage_platform_unreachable') from None
    if len(raw) > MAX_RESPONSE:
        raise transport.BackupError('storage response exceeds its limit')
    try:
        value = json.loads(raw)
    except ValueError:
        raise transport.BackupError('storage response is invalid') from None
    if not isinstance(value, dict):
        raise transport.BackupError('storage response must be an object')
    return value


def validate_binding(profile, value):
    own = identity(profile)
    if value.get('schemaVersion') != 1 or value.get('enabled') is not True or any(value.get(k) != v for k, v in own.items()):
        raise transport.BackupError('storage binding identity differs')
    if value.get('credentialsEndpoint') != API + 'storage-credentials':
        raise transport.BackupError('storage credential endpoint is not the fixed machine route')
    backup = validate_scope(profile, value.get('backup'), 'backup')
    business = validate_scope(profile, value['business'], 'business') if value.get('business') is not None else None
    policy = value.get('backupPolicy')
    if not isinstance(policy, dict) or policy.get('enabled') is not True or policy.get('automaticEnrollment') is not True:
        raise transport.BackupError('automatic backup policy is not enabled')
    hours = policy.get('intervalHours')
    keep = policy.get('localKeep')
    if type(hours) is not int or not 1 <= hours <= 168 or type(keep) is not int or not 2 <= keep <= 14:
        raise transport.BackupError('backup policy is unsupported')
    revision = value.get('revision')
    slugs = value.get('applicationSlugs')
    if type(revision) is not int or revision < 1 or not isinstance(slugs, list) or len(slugs) > 256 or len(set(slugs)) != len(slugs):
        raise transport.BackupError('storage binding revision or application set is invalid')
    for slug in slugs:
        transport.valid_slug(slug)
    return {**own, 'schemaVersion': 1, 'enabled': True, 'business': business, 'backup': backup,
            'revision': revision, 'applicationSlugs': slugs,
            'backupPolicy': dict(policy), 'credentialProvider': 'platform-sts-v1'}


def credential_values(path):
    transport.private_file(path)
    if path.stat().st_size > 65536:
        raise transport.BackupError('storage credential file is too large')
    values = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            raise transport.BackupError('storage credential file is invalid')
        key, value = line.split('=', 1)
        if key in values or any(c in value for c in '\r\n\x00'):
            raise transport.BackupError('storage credential field is invalid')
        values[key] = value.strip().strip('\"\'')
    return values


def lease_file(purpose):
    if purpose == 'business':
        return BUSINESS_FILE
    if purpose == 'backup':
        return BACKUP_FILE
    raise transport.BackupError('storage purpose is invalid')


def validate_lease(profile, purpose, response, scope, now=None):
    own = identity(profile)
    if response.get('schemaVersion') != 1 or response.get('purpose') != purpose or any(response.get(k) != v for k, v in own.items()):
        raise transport.BackupError('storage lease identity differs')
    revision = profile.get('platformStorageBinding', {}).get('revision')
    if type(response.get('revision')) is not int or response['revision'] != revision:
        raise transport.BackupError('storage lease binding revision differs')
    returned_scope = validate_scope(profile, response, purpose)
    if any(returned_scope[k] != scope[k] for k in ('bucket', 'region', 'rootPrefix')):
        raise transport.BackupError('storage lease scope changed')
    fields = response.get('credentials')
    if not isinstance(fields, dict):
        raise transport.BackupError('storage lease has no credentials')
    for key, maximum in {'accessKeyId': 256, 'accessKeySecret': 512, 'securityToken': 32768}.items():
        value = fields.get(key)
        if not isinstance(value, str) or not value or len(value) > maximum or any(c in value for c in '\r\n\x00'):
            raise transport.BackupError('storage lease credential field is invalid')
    now = now or dt.datetime.now(UTC)
    expires = parse_time(fields.get('expiresAt'))
    if not now + dt.timedelta(seconds=180) < expires <= now + dt.timedelta(hours=12):
        raise transport.BackupError('storage lease lifetime is invalid')
    return {'OSS_ENDPOINT': scope['endpoint'], 'OSS_BUCKET': scope['bucket'],
            'OSS_ACCESS_KEY_ID': fields['accessKeyId'], 'OSS_ACCESS_KEY_SECRET': fields['accessKeySecret'],
            'OSS_SECURITY_TOKEN': fields['securityToken'], 'OSS_EXPIRES_AT': fields['expiresAt'],
            'OSS_CREDENTIAL_PROVIDER': 'platform-sts-v1', 'OSS_ORGANIZATION_ID': own['organizationId'],
            'OSS_ENVIRONMENT': own['environment'], 'OSS_RUNTIME_ID': own['runtimeId'],
            'OSS_PURPOSE': purpose, 'OSS_ROOT_PREFIX': scope['rootPrefix']}


def write_credentials(path, values):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    parent = path.parent.lstat()
    if path.parent.is_symlink() or (os.name == 'posix' and (parent.st_uid != 0 or parent.st_mode & 0o077)):
        raise transport.BackupError('storage credential directory must be private')
    if path.exists():
        transport.private_file(path)
    payload = '# ' + MARKER + '\n' + ''.join(k + '=' + v + '\n' for k, v in values.items())
    atomic_private_bytes(path, payload.encode())


def atomic_private_bytes(path, payload, mode=0o600):
    import tempfile
    fd, name = tempfile.mkstemp(prefix='.lease-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def persist_profile(value):
    mode = stat.S_IMODE(transport.private_file(PROFILE, allow_metadata_read=True).st_mode) if PROFILE.exists() else 0o600
    atomic_private_bytes(PROFILE, transport.json_bytes(value), mode)


@contextlib.contextmanager
def renewal_lock(path):
    with transport.publication_lock_wait(path, 35):
        yield


def renew(profile, purpose, *, call=platform_call, destination=None, force=False):
    binding = profile.get('platformStorageBinding') or {}
    scope = validate_scope(profile, binding.get(purpose), purpose)
    path = Path(destination) if destination is not None else lease_file(purpose)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with renewal_lock(path.parent / ('.' + path.name + '.renew.lock')):
        previous = credential_values(path) if path.exists() else None
        now = dt.datetime.now(UTC)
        if previous and previous.get('OSS_CREDENTIAL_PROVIDER') == 'platform-sts-v1':
            if previous.get('OSS_BUCKET') != scope['bucket'] or previous.get('OSS_ENDPOINT') != scope['endpoint']:
                raise transport.BackupError('existing storage lease scope differs')
            own = identity(profile)
            if any(previous.get(k) != expected for k, expected in {'OSS_ORGANIZATION_ID': own['organizationId'],
                    'OSS_ENVIRONMENT': own['environment'], 'OSS_RUNTIME_ID': own['runtimeId'],
                    'OSS_PURPOSE': purpose, 'OSS_ROOT_PREFIX': scope['rootPrefix']}.items()):
                raise transport.BackupError('existing storage lease identity differs')
            if not force and parse_time(previous.get('OSS_EXPIRES_AT')) > now + dt.timedelta(seconds=REFRESH_MARGIN):
                return previous
        response = call(profile, 'storage-credentials', {'purpose': purpose})
        lease_profile = profile
        if response.get('revision') != binding.get('revision'):
            latest = validate_binding(profile, call(profile, 'storage-profile'))
            latest_scope = latest.get(purpose)
            if latest_scope is None or any(latest_scope[k] != scope[k] for k in ('bucket', 'region', 'rootPrefix')):
                raise transport.BackupError('storage_profile_changed')
            lease_profile = {**profile, 'platformStorageBinding': latest}
        values = validate_lease(lease_profile, purpose, response, scope, now)
        write_credentials(path, values)
        return values


class RuntimeCredentialsProvider:
    """Official oss2 calls this before every request/signature, including parts."""
    def __init__(self, profile, purpose, path, *, refresher=renew):
        self.profile, self.purpose, self.path = profile, purpose, Path(path)
        self.refresher = refresher

    def get_credentials(self):
        values = self.refresher(self.profile, self.purpose, destination=self.path)
        if parse_time(values.get('OSS_EXPIRES_AT')) <= dt.datetime.now(UTC):
            raise transport.BackupError('storage lease expired')
        from oss2.credentials import Credentials
        return Credentials(values['OSS_ACCESS_KEY_ID'], values['OSS_ACCESS_KEY_SECRET'], values['OSS_SECURITY_TOKEN'])


def plan_module():
    candidates = [Path(__file__).with_name('runtime_backup_plan.py'), Path('/usr/local/lib/zhuojian/runtime_backup_plan.py')]
    for path in candidates:
        if path.is_file() and not path.is_symlink():
            spec = importlib.util.spec_from_file_location('zhuojian_runtime_backup_plan', path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise transport.BackupError('backup enrollment helper is not installed')


def command(argv, *, check=True):
    result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    if check and result.returncode:
        raise transport.BackupError('storage service operation failed')
    return result


def enroll(profile, slug=None, *, require_new=False, wait_seconds=0):
    with transport.publication_lock_wait(Path('/run/lock/zhuojian-runtime-admin.lock'), wait_seconds):
        if PROFILE.exists():
            fresh = transport.read_json(PROFILE, allow_metadata_read=True)
            if identity(fresh) != identity(profile):
                raise transport.BackupError('runtime_identity_changed')
            profile = fresh
        return plan_module().enroll(profile, plan_path=PLAN, selected=slug, require_new=require_new)


def refresh_binding(profile, *, call=platform_call):
    """Policy/revision renewal is safe only inside the original storage scope."""
    binding = validate_binding(profile, call(profile, 'storage-profile'))
    existing = profile.get('backupStorage') or {}
    if any(existing.get(k) != binding['backup'][k] for k in ('bucket', 'region', 'rootPrefix')):
        raise transport.BackupError('storage_profile_changed')
    previous = profile.get('platformStorageBinding') or {}
    if previous.get('business') is None:
        binding['business'] = None
    elif binding['business'] is None or any(previous['business'].get(k) != binding['business'][k] for k in ('bucket', 'region', 'rootPrefix')):
        raise transport.BackupError('storage_profile_changed')
    # Preserve the same-bucket registered internal/public transport choice.
    for purpose in ('business', 'backup'):
        if binding.get(purpose) is not None and previous.get(purpose) is not None:
            binding[purpose]['endpoint'] = previous[purpose]['endpoint']
    candidate = {**profile, 'platformStorageBinding': binding}
    persist_profile(candidate)
    return candidate


def report(profile, *, call=platform_call):
    import runtime_recovery_evidence as evidence
    plan = transport.read_json(PLAN)
    current_binding = validate_binding(profile, call(profile, 'storage-profile'))
    existing = profile.get('backupStorage') or {}
    if any(existing.get(k) != current_binding['backup'][k] for k in ('bucket', 'region', 'rootPrefix')):
        raise transport.BackupError('storage_report_binding_changed')
    authoritative = current_binding['applicationSlugs']
    reported_plan = {**plan, 'applications': {slug: plan['applications'].get(slug, {'name': slug}) for slug in authoritative}}
    projection = evidence.observe(profile, reported_plan)
    systems = []
    covered = failed = pending = 0
    for value in projection['systems']:
        point = value['latest_successful_point']
        if point is not None:
            point = dict(point)
            point['project_ids'] = []
        job = value['latest_job']
        app = plan['applications'].get(value['application_slug']) or {}
        ready = bool(app.get('primary_sqlite')) and app.get('enrollment', {}).get('status', 'ready') == 'ready'
        status = 'pending' if not ready else 'failed' if job.get('status') == 'failed' else 'covered'
        covered += status == 'covered'
        pending += status == 'pending'
        failed += status == 'failed'
        systems.append({'applicationSlug': value['application_slug'], 'enrollmentStatus': status,
                        'latestJob': job, 'latestSuccessfulPoint': point})
    timer_unit = profile.get('backupSchedule', {}).get('timerUnit', 'zhuojian-storage-backup.timer')
    if not isinstance(timer_unit, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.@-]{0,120}\.timer', timer_unit):
        raise transport.BackupError('registered backup timer name is invalid')
    timer = command(['systemctl', 'is-enabled', timer_unit], check=False)
    value = {'schemaVersion': 1, **identity(profile), 'bindingRevision': current_binding['revision'],
             'observedAt': dt.datetime.now(UTC).isoformat(), 'agentVersion': '1.0.0',
             'schedule': {'enabled': timer.returncode == 0, 'nextRunAt': None},
             'enrollment': {'registered': len(systems), 'covered': covered, 'pending': pending, 'failed': failed}, 'systems': systems}
    call(profile, 'storage-report', value)
    return {'reported': True, 'systems': len(systems), 'covered': covered, 'pending': pending}


def configure(profile, *, call=platform_call):
    binding = validate_binding(profile, call(profile, 'storage-profile'))
    previous = profile.get('backupStorage')
    backup = binding['backup']
    if previous and any(previous.get(k) != backup[k] for k in ('bucket', 'region', 'rootPrefix')):
        raise transport.BackupError('existing backup scope differs; explicit migration is required')
    if previous and previous.get('credentialRef', str(BACKUP_FILE)) != str(BACKUP_FILE):
        raise transport.BackupError('existing backup credential path requires an explicit adoption plan')
    if BACKUP_FILE.exists():
        old_values = credential_values(BACKUP_FILE)
        internal = f"https://oss-{backup['region']}-internal.aliyuncs.com"
        public = f"https://oss-{backup['region']}.aliyuncs.com"
        if old_values.get('OSS_BUCKET') == backup['bucket'] and old_values.get('OSS_ENDPOINT') in {internal, public}:
            backup['endpoint'] = old_values['OSS_ENDPOINT']
    business = binding['business']
    current = profile.get('objectStorage')
    preserved = False
    if current and business and any(current.get(k) != business[k] for k in ('bucket', 'region', 'rootPrefix')):
        binding['business'] = None
        preserved = True
    candidate = {**profile, 'platformStorageBinding': binding}
    # Claim only the same existing backup namespace. Cloud credentials remain
    # separate from business access; no source Delete or cloud admin is added.
    candidate['backupStorage'] = {'provider': 'aliyun-oss', 'namespaceMode': 'enterprise-v1',
            **{k: backup[k] for k in ('bucket', 'region', 'rootPrefix')}, 'credentialRef': str(BACKUP_FILE),
            'credentialProvider': 'platform-sts-v1'}
    # Fetch and test in a private staging directory before touching any active
    # key/profile. Lease writers are serialized independently of backup work.
    paths = [BACKUP_FILE] + ([BUSINESS_FILE] if binding['business'] is not None else [])
    with contextlib.ExitStack() as locks:
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            locks.enter_context(renewal_lock(path.parent / ('.' + path.name + '.renew.lock')))
        with tempfile.TemporaryDirectory(prefix='.storage-stage-', dir=PROFILE.parent) as directory:
            stage = Path(directory)
            os.chmod(stage, 0o700)
            staged_backup = stage / 'backup.env'
            backup_values = validate_lease(candidate, 'backup', call(candidate, 'storage-credentials', {'purpose': 'backup'}), backup)
            write_credentials(staged_backup, backup_values)
            probe_profile = {**candidate, 'backupStorage': {**candidate['backupStorage'], 'credentialRef': str(staged_backup)}}
            scope = transport.BackupScope(probe_profile)
            backend = transport.OssBackend(scope)
            backend.assert_scope(scope)
            backend.require_versioning()
            candidate['backupStorage']['boundaryVerified'] = True
            payloads = {BACKUP_FILE: staged_backup.read_bytes()}
            if binding['business'] is not None:
                values = validate_lease(candidate, 'business', call(candidate, 'storage-credentials', {'purpose': 'business'}), binding['business'])
                staged_business = stage / 'business.env'
                write_credentials(staged_business, values)
                payloads[BUSINESS_FILE] = staged_business.read_bytes()
                legacy = Path('/etc/zhuojian/oss-gateway.env')
                if not legacy.exists():
                    payloads[legacy] = payloads[BUSINESS_FILE]
            # Profile first is intentional: an old static key remains usable
            # with the same scope, while a new STS key must find its binding.
            ordered = {PROFILE: transport.json_bytes(candidate), **payloads}
            commit_configuration(ordered)
    return candidate, {'configured': True, 'businessLegacyPreserved': preserved or business is None,
                       'uploadVerified': False, 'recoveryVerified': False}


def commit_configuration(payloads):
    snapshots = {}
    for path in payloads:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        parent = path.parent.lstat()
        if path.parent.is_symlink() or (os.name == 'posix' and (parent.st_uid != 0 or parent.st_mode & 0o077)):
            raise transport.BackupError('storage configuration directory is unsafe')
        if path.is_symlink():
            raise transport.BackupError('storage configuration cannot replace a symlink')
        if path.exists():
            info = transport.private_file(path, allow_metadata_read=path == PROFILE)
            snapshots[path] = (path.read_bytes(), stat.S_IMODE(info.st_mode))
        else:
            snapshots[path] = (None, 0o600)
    try:
        for path, payload in payloads.items():
            old, mode = snapshots[path]
            if (path.read_bytes() if path.exists() else None) != old:
                raise transport.BackupError('storage_configuration_changed')
            atomic_private_bytes(path, payload, mode)
    except BaseException:
        # Check every prepared target, even if interruption arrived immediately
        # after rename and before the writer returned. Never undo other work.
        conflict = False
        for path, payload in reversed(list(payloads.items())):
            old, mode = snapshots[path]
            current = path.read_bytes() if path.exists() and not path.is_symlink() else None
            if current == old:
                continue
            if path.is_symlink() or current != payload:
                conflict = True
                continue
            if old is None:
                path.unlink()
            else:
                atomic_private_bytes(path, old, mode)
        if conflict:
            raise transport.BackupError('storage_rollback_conflict') from None
        raise


def unit_contents(interval):
    common = '\n# ' + MARKER + '\n'
    limits = 'User=root\nUMask=0077\nNice=10\nCPUQuota=100%\nMemoryMax=1536M\nTasksMax=256\nIOSchedulingClass=best-effort\nIOSchedulingPriority=7\n'
    return {
        'zhuojian-storage-refresh.service': '[Unit]\nDescription=Refresh scoped Runtime storage leases and report metadata\n' + common + '[Service]\nType=oneshot\n' + limits + 'ExecStart=/usr/local/sbin/zhuojian-storage-bootstrap refresh\nTimeoutStartSec=180\n',
        'zhuojian-storage-refresh.timer': '[Unit]\nDescription=Refresh Runtime storage leases\n' + common + '[Timer]\nOnBootSec=90s\nOnUnitActiveSec=2min\nPersistent=true\n[Install]\nWantedBy=timers.target\n',
        'zhuojian-storage-backup.service': '[Unit]\nDescription=Online Runtime backup and isolated restore\n' + common + '[Service]\nType=oneshot\n' + limits + 'ExecStart=/usr/local/sbin/zhuojian-storage-bootstrap backup\nTimeoutStartSec=7200\n',
        'zhuojian-storage-backup.timer': '[Unit]\nDescription=Online Runtime data protection\n' + common + f'[Timer]\nOnBootSec=10min\nOnUnitActiveSec={interval}h\nPersistent=true\n[Install]\nWantedBy=timers.target\n',
        'zhuojian-initial-backup@.service': '[Unit]\nDescription=First verified online recovery point for %i\n' + common + '[Service]\nType=oneshot\n' + limits + 'ExecStart=/usr/local/sbin/zhuojian-storage-bootstrap backup --application-slug %i\nTimeoutStartSec=7200\n',
        'zhuojian-business-lease.service': '[Unit]\nDescription=Business-only OSS credential renewal socket\n' + common + '[Service]\nType=simple\nUser=root\nUMask=0077\nRuntimeDirectory=zhuojian-oss-lease/business\nRuntimeDirectoryMode=0700\nRuntimeDirectoryPreserve=yes\nExecStart=/usr/local/sbin/zhuojian-storage-bootstrap serve-business\nRestart=on-failure\nRestartSec=5\nMemoryMax=128M\nTasksMax=32\n[Install]\nWantedBy=multi-user.target\n',
    }


def install_units(profile, *, preserve_existing_schedule=False, existing_timer=None):
    if preserve_existing_schedule and (not isinstance(existing_timer, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.@-]{0,120}\.timer', existing_timer)):
        raise transport.BackupError('existing backup timer must be explicitly registered before preserving its schedule')
    root = Path('/etc/systemd/system')
    units = unit_contents(profile['platformStorageBinding']['backupPolicy']['intervalHours'])
    for name, content in units.items():
        path = root / name
        if path.exists():
            info = path.lstat()
            if path.is_symlink() or not stat.S_ISREG(info.st_mode) or (os.name == 'posix' and (info.st_uid != 0 or info.st_mode & 0o022)):
                raise transport.BackupError('existing storage unit is unsafe')
            if MARKER not in path.read_text():
                raise transport.BackupError('existing storage unit has another owner')
        fd, temporary = __import__('tempfile').mkstemp(prefix='.storage-unit-', dir=root)
        with os.fdopen(fd, 'w') as handle:
            handle.write(content)
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    command(['systemd-analyze', 'verify', *[str(root / name) for name in units if name.endswith('.service')]])
    command(['systemctl', 'daemon-reload'])
    command(['systemctl', 'enable', '--now', 'zhuojian-storage-refresh.timer', 'zhuojian-business-lease.service'])
    if not preserve_existing_schedule:
        command(['systemctl', 'enable', '--now', 'zhuojian-storage-backup.timer'])
        old = root / 'zhuojian-backup.service'
        if old.exists() and 'ExecStart=/usr/local/sbin/zhuojian-runtime backup-all' in old.read_text():
            command(['systemctl', 'disable', '--now', 'zhuojian-backup.timer'])
    return {'installed': True, 'existingSchedulePreserved': preserve_existing_schedule}


def serve_business():
    """Only the gateway receives this mount; no client-selected purpose/path."""
    SOCKET_DIRECTORY.mkdir(parents=True, exist_ok=True, mode=0o700)
    info = SOCKET_DIRECTORY.lstat()
    if SOCKET_DIRECTORY.is_symlink() or info.st_uid != 0 or info.st_mode & 0o077:
        raise transport.BackupError('business lease socket directory is unsafe')
    if SOCKET_PATH.exists():
        info = SOCKET_PATH.lstat()
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid != 0:
            raise transport.BackupError('unknown business lease socket path')
        probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        probe.settimeout(2)
        try:
            probe.connect(str(SOCKET_PATH))
        except ConnectionRefusedError:
            SOCKET_PATH.unlink()
        else:
            raise transport.BackupError('business lease broker is already running')
        finally:
            probe.close()

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            self.request.settimeout(5)
            try:
                _, uid, _ = struct.unpack('3i', self.request.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                incoming = b''
                while not incoming.endswith(b'\n') and len(incoming) < 32:
                    block = self.request.recv(32 - len(incoming))
                    if not block:
                        break
                    incoming += block
                if uid != 0 or incoming != b'GET\n':
                    return
                profile = transport.read_json(PROFILE, allow_metadata_read=True)
                values = renew(profile, 'business')
                self.request.sendall(json.dumps({'ok': True, 'credentials': values}, separators=(',', ':')).encode() + b'\n')
            except Exception:
                with contextlib.suppress(OSError):
                    self.request.sendall(b'{"ok":false,"error":"business_lease_unavailable"}\n')

    class Server(socketserver.ThreadingUnixStreamServer):
        daemon_threads = True
        request_queue_size = 16

    with Server(str(SOCKET_PATH), Handler) as server:
        os.chmod(SOCKET_PATH, 0o600)
        server.serve_forever(poll_interval=1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['configure', 'refresh', 'enroll', 'backup', 'report', 'serve-business'])
    parser.add_argument('--application-slug')
    parser.add_argument('--preserve-existing-schedule', action='store_true')
    parser.add_argument('--existing-backup-timer')
    args = parser.parse_args(argv)
    try:
        if os.name != 'posix' or os.geteuid() != 0:
            raise transport.BackupError('storage bootstrap requires Runtime root')
        if args.command == 'serve-business':
            serve_business()
            return 0
        profile = transport.read_json(PROFILE, allow_metadata_read=True)
        if args.application_slug is not None:
            transport.valid_slug(args.application_slug)
        if args.command == 'configure':
            if args.preserve_existing_schedule and (not args.existing_backup_timer or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.@-]{0,120}\.timer', args.existing_backup_timer)):
                raise transport.BackupError('existing backup timer name is required')
            with transport.publication_lock(Path('/run/lock/zhuojian-runtime-admin.lock')):
                profile = transport.read_json(PROFILE, allow_metadata_read=True)
                profile, result = configure(profile)
                profile['backupSchedule'] = {'timerUnit': args.existing_backup_timer if args.preserve_existing_schedule else 'zhuojian-storage-backup.timer'}
                persist_profile(profile)
            enrollment = enroll(profile)
            result.update(enrollment=enrollment, schedule=install_units(profile, preserve_existing_schedule=args.preserve_existing_schedule, existing_timer=args.existing_backup_timer))
            result['report'] = report(profile)
            if not args.preserve_existing_schedule:
                queued = command(['systemctl', 'start', '--no-block', 'zhuojian-storage-backup.service'], check=False)
                result['initialBackupQueued'] = queued.returncode == 0
        elif args.command in {'refresh', 'backup'}:
            if args.command == 'backup':
                with transport.publication_lock_wait(Path('/run/lock/zhuojian-runtime-admin.lock'), 6600):
                    profile = transport.read_json(PROFILE, allow_metadata_read=True)
                    profile = refresh_binding(profile)
            else:
                try:
                    with transport.publication_lock(Path('/run/lock/zhuojian-runtime-admin.lock')):
                        profile = transport.read_json(PROFILE, allow_metadata_read=True)
                        profile = refresh_binding(profile)
                except BlockingIOError:
                    # Renewal/reporting do not need to mutate the Runtime while
                    # a long online job owns its lock; per-signature renewal
                    # still checks the live binding revision and fixed scope.
                    pass
            for purpose in ('backup', 'business'):
                if profile.get('platformStorageBinding', {}).get(purpose) is not None:
                    renew(profile, purpose)
            if args.command == 'backup':
                enroll(profile, args.application_slug, require_new=True, wait_seconds=6600)
                import runtime_online_backup
                keep = profile.get('platformStorageBinding', {}).get('backupPolicy', {}).get('localKeep', 2)
                code = runtime_online_backup.main(['--publish', '--verify-restore', '--keep-local', str(keep), '--lock-wait-seconds', '6600', args.application_slug or 'all'])
                result = {'backupExitCode': code, 'report': report(profile)}
                print(json.dumps(result))
                return code
            result = {'refreshed': True, 'report': report(profile)}
        elif args.command == 'enroll':
            result = {'enrollment': enroll(profile, args.application_slug, require_new=True)}
        else:
            result = report(profile)
        print(json.dumps({'ok': True, **result}))
        return 0
    except Exception as exc:
        message = str(exc)
        code = message if isinstance(exc, transport.BackupError) and re.fullmatch(r'[a-z][a-z0-9_]{0,79}', message) else 'storage_bootstrap_failed'
        print(json.dumps({'ok': False, 'error_code': code}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
