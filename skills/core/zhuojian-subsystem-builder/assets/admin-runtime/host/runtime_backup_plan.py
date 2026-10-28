"""Root-owned automatic backup enrollment; never changes business storage or data."""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import tempfile

MARKER = 'zhuojian-runtime-backup-enrollment/v1'
SLUG = re.compile(r'^[a-z0-9][a-z0-9-]{0,62}$')
MAXIMUM_FILES = 10000


def read_json(path, *, metadata=False):
    path = Path(path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_size > 4 * 1024**2:
        raise ValueError('unsafe backup enrollment metadata')
    if os.name == 'posix' and (info.st_uid != 0 or info.st_mode & (0o022 if metadata else 0o077)):
        raise ValueError('backup enrollment metadata permissions are unsafe')
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('backup enrollment metadata must be an object')
    return value


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.is_symlink() or (path.exists() and path.is_symlink()):
        raise ValueError('backup enrollment target cannot be a symlink')
    fd, name = tempfile.mkstemp(prefix='.enrollment-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True).encode())
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(name, 0o600)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def environment_values(path):
    path = Path(path)
    info = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_size > 1024**2:
        raise ValueError('application configuration is unsafe')
    if os.name == 'posix' and (info.st_uid != 0 or info.st_mode & 0o077):
        raise ValueError('application configuration must be private')
    values = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip().strip('\"\'')
    return values


def discover_database(release):
    """Identify actual SQLite bytes; unsupported/ambiguous stores stay pending."""
    root = Path(release['dataDir'])
    if root.is_symlink() or not root.is_dir():
        return {'status': 'pending', 'reason': 'data_directory_unavailable'}
    values = environment_values(release['envFile'])
    urls = sorted({v for k, v in values.items() if k in {'DATABASE_URL', 'SQLALCHEMY_DATABASE_URI', 'DB_URL'} and v})
    if any(not value.startswith('sqlite:') for value in urls) or any(values.get(k) for k in ('DB_HOST', 'DATABASE_HOST', 'PGHOST', 'MYSQL_HOST')):
        kind = ('postgresql' if values.get('PGHOST') or any(v.startswith(('postgres:', 'postgresql:', 'postgresql+')) for v in urls)
                else 'mysql' if values.get('MYSQL_HOST') or any(v.startswith(('mysql:', 'mysql+', 'mariadb:')) for v in urls)
                else 'external')
        return {'status': 'pending', 'reason': 'database_adapter_required', 'database_kind': kind}
    databases = []
    count = 0
    for directory, dirs, names in os.walk(root, followlinks=False):
        if any((Path(directory) / name).is_symlink() for name in dirs):
            return {'status': 'pending', 'reason': 'data_symlink_requires_review'}
        for name in names:
            count += 1
            if count > MAXIMUM_FILES:
                return {'status': 'pending', 'reason': 'database_discovery_bound_exceeded'}
            path = Path(directory) / name
            if path.is_symlink() or not path.is_file():
                return {'status': 'pending', 'reason': 'data_special_file_requires_review'}
            if name.endswith(('-wal', '-shm', '-journal')):
                continue
            with path.open('rb') as handle:
                if handle.read(16) == b'SQLite format 3\x00':
                    databases.append('/data/' + path.relative_to(root).as_posix())
    if any(not value.startswith('sqlite:////') for value in urls):
        return {'status': 'pending', 'reason': 'declared_sqlite_path_requires_review', 'database_kind': 'sqlite'}
    explicit = [value.removeprefix('sqlite:///') for value in urls]
    explicit += [values[k] for k in ('DATABASE_PATH', 'SQLITE_PATH', 'SQLITE_DATABASE_PATH') if values.get(k)]
    explicit = sorted(set(explicit))
    if len(explicit) == 1 and explicit[0] in databases:
        primary = explicit[0]
    elif explicit:
        return {'status': 'pending', 'reason': 'declared_sqlite_not_in_verified_mount', 'database_kind': 'sqlite'}
    elif len(databases) == 1:
        primary = databases[0]
    else:
        return {'status': 'pending', 'reason': 'database_not_identified' if not databases else 'ambiguous_sqlite_databases'}
    source = root / primary.removeprefix('/data/')
    with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=2) as database:
        database.execute('PRAGMA query_only=ON')
        columns = {row[1] for row in database.execute('PRAGMA table_info(stored_files)')}
    if not {'storage_key', 'storage_backend', 'deletion_state', 'size', 'sha256'} <= columns:
        return {'status': 'pending', 'reason': 'file_reference_adapter_required', 'database_kind': 'sqlite'}
    return {'status': 'ready', 'method': 'sqlite_magic_and_runtime_mount', 'primary_sqlite': primary, 'database_kind': 'sqlite'}


def enroll(profile, *, plan_path=Path('/etc/zhuojian/backup-online-plan.json'), selected=None, require_new=False):
    """Caller owns the Runtime lock. Existing reviewed app plans are preserved."""
    plan_path = Path(plan_path)
    identity = {key: profile[key] for key in ('organizationId', 'runtimeId', 'environment')}
    if plan_path.exists():
        plan = read_json(plan_path)
        if any(plan.get(k) != v for k, v in identity.items()) or not isinstance(plan.get('applications'), dict):
            raise ValueError('backup plan belongs to another Runtime')
    else:
        plan = {**identity, 'schemaVersion': 1, 'source_id': 'runtime:' + profile['runtimeId'],
                'host_id': 'runtime:' + profile['runtimeId'], 'applications': {}}
    releases = Path(profile.get('deployment', {}).get('deploymentsRoot', '/srv/zhuojian/deployments'))
    results = {}
    for path in sorted(releases.glob('*/release.json')):
        slug = path.parent.name
        if not SLUG.fullmatch(slug) or (selected is not None and slug != selected):
            continue
        try:
            release = read_json(path, metadata=True)
        except (OSError, ValueError):
            discovery = {'status': 'pending', 'reason': 'release_metadata_unavailable'}
            results[slug] = discovery
            if slug not in plan['applications']:
                plan['applications'][slug] = {'name': slug, 'project_id': None,
                    'initialProtectionRequired': require_new,
                    'enrollment': {**discovery, 'managedBy': MARKER}}
            continue
        if release.get('applicationSlug') != slug or release.get('managedBy') != 'zhuojian-runtime-admin/v1':
            continue
        if not (release.get('current') or {}).get('commit'):
            continue
        if slug in plan['applications']:
            app = plan['applications'][slug]
            if app.get('primary_sqlite'):
                results[slug] = {'status': 'ready', 'existingReviewedPlanPreserved': True}
                continue
            if app.get('enrollment', {}).get('managedBy') != MARKER:
                results[slug] = {'status': 'pending', 'reason': 'existing_plan_requires_review'}
                continue
        else:
            app = {'name': slug, 'project_id': None}
            if require_new:
                app['initialProtectionRequired'] = True
        try:
            discovery = discover_database(release)
        except (OSError, ValueError, sqlite3.Error):
            discovery = {'status': 'pending', 'reason': 'database_discovery_failed'}
        if discovery.get('primary_sqlite'):
            app['primary_sqlite'] = discovery['primary_sqlite']
        app['enrollment'] = {**discovery, 'managedBy': MARKER,
                             'observedCommit': (release.get('current') or {}).get('commit'),
                             'observedAt': dt.datetime.now(dt.timezone.utc).isoformat()}
        plan['applications'][slug] = app
        results[slug] = discovery
    atomic_json(plan_path, plan)
    return results


def protection_status(profile, slug, commit, *, plan_path=Path('/etc/zhuojian/backup-online-plan.json')):
    """Require same-point cloud readback and real data/reference/Git restore receipts."""
    if not profile.get('platformStorageBinding', {}).get('enabled'):
        return {'required': False, 'status': 'legacy_not_enforced'}
    if not Path(plan_path).is_file():
        return {'required': True, 'status': 'pending_enrollment'}
    plan = read_json(plan_path)
    app = plan.get('applications', {}).get(slug)
    if not app:
        return {'required': True, 'status': 'pending_enrollment'}
    required = app.get('initialProtectionRequired') is True
    root = Path(profile.get('deployment', {}).get('backupsRoot', '/srv/zhuojian/backups')) / slug
    for path in sorted(root.glob('*.tar.gz.json'), reverse=True):
        try:
            metadata = read_json(path)
            if metadata.get('applicationSlug') != slug or metadata.get('commit') != commit or metadata.get('schemaVersion') != 3:
                continue
            archive = path.name.removesuffix('.json')
            remote = read_json(root / (archive + '.remote.json'))
            restored = read_json(root / (archive + '.restore.json'))
            sha = metadata.get('sha256')
            if not re.fullmatch(r'[a-f0-9]{64}', str(sha)):
                continue
            if any(remote.get(k) != profile[k] for k in ('organizationId', 'runtimeId', 'environment')):
                continue
            if (remote.get('applicationSlug') != slug or remote.get('archive') != archive or remote.get('sha256') != sha
                    or remote.get('offServer') is not True or not remote.get('fullReadbackAt') or not remote.get('versionId')):
                continue
            if (restored.get('archiveName') != archive or restored.get('sha256') != sha
                    or restored.get('versionId') != remote['versionId'] or any(restored.get(k) is not True for k in
                    ('businessDatabaseVerified', 'fileHashesVerified', 'referenceIntegrityVerified', 'gitVerified', 'referencesRequeried'))):
                continue
            return {'required': required, 'status': 'verified', 'pointId': archive, 'commit': commit}
        except (OSError, ValueError, KeyError):
            continue
    return {'required': required, 'status': 'pending_first_verified_point',
            'reason': app.get('enrollment', {}).get('reason')}
