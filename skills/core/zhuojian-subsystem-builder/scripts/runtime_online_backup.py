#!/usr/bin/env python3
"""Online SQLite/data/object recovery points; never stops or executes business apps.

The operator supplies a protected, reviewed plan of actual SQLite locations. This
does not infer databases from empty data directories or change existing storage.
Private manifests remain inside the encrypted/private backup namespace.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from urllib.parse import urlsplit

import runtime_backup_oss as transport

MARKER = 'zhuojian-runtime-online-backup/v1'
MANAGED_BY = transport.MANAGED_BY
FLOOR = 5 * 1024**3
MAX_FILES = 100000
CHUNK = 1024 * 1024
SQL_NAME = re.compile(r'^[A-Za-z_][A-Za-z0-9_]{0,99}$')


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def relative_key(value):
    if not isinstance(value, str) or not value or len(value.encode()) > 1024:
        raise transport.BackupError('invalid recovery member')
    p = PurePosixPath(value)
    if p.is_absolute() or '\\' in value or ':' in value or any(x in {'', '.', '..'} for x in value.split('/')) or any(ord(x) < 32 for x in value):
        raise transport.BackupError('unsafe recovery member')
    return value


def run(argv, timeout=180):
    result = subprocess.run(argv, capture_output=True, timeout=timeout)
    if result.returncode:
        raise transport.BackupError('recovery source command failed')
    return result.stdout.decode()


def ensure_space(path, needed=0, floor=FLOOR):
    if shutil.disk_usage(path).free < floor + needed:
        raise transport.BackupError('online backup capacity floor would be exceeded')


def file_digest(path):
    return transport.sha_file(Path(path))


def signature(value):
    # Windows lstat/fstat may disagree about creation-time metadata after an
    # atomic rename. Linux retains ctime checking; both also rehash the source.
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns if os.name != 'nt' else None


def plain_file(path):
    value = path.lstat()
    if not stat.S_ISREG(value.st_mode) or path.is_symlink():
        raise transport.BackupError('source must be a regular file without symlinks')
    return value


def source_permissions(info):
    return {'uid':info.st_uid,'gid':info.st_gid,'mode':stat.S_IMODE(info.st_mode)}


def copy_stable(source, destination, *, floor=FLOOR):
    before = plain_file(source)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    ensure_space(destination.parent, before.st_size, floor)
    digest = hashlib.sha256(); size = 0
    fd = os.open(source, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0))
    with os.fdopen(fd, 'rb') as incoming, destination.open('xb') as outgoing:
        if signature(os.fstat(incoming.fileno())) != signature(before):
            raise transport.BackupError('source changed before copy')
        os.chmod(destination, 0o600)
        while block := incoming.read(CHUNK):
            ensure_space(destination.parent, len(block), floor)
            outgoing.write(block); digest.update(block); size += len(block)
        outgoing.flush(); os.fsync(outgoing.fileno())
        if signature(os.fstat(incoming.fileno())) != signature(before):
            raise transport.BackupError('source changed during copy')
    if signature(plain_file(source)) != signature(before) or size != before.st_size:
        raise transport.BackupError('source changed after copy')
    # Detect an in-place rewrite even if a writer restores the timestamps.
    if file_digest(source) != (digest.hexdigest(), size):
        raise transport.BackupError('source content changed after copy')
    return {'sha256': digest.hexdigest(), 'bytes': size,'source_permissions':source_permissions(before)}


def verify_sqlite(path):
    connection = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=2)
    try:
        connection.execute('PRAGMA query_only=ON')
        if connection.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise transport.BackupError('isolated database integrity check failed')
        if connection.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise transport.BackupError('isolated database foreign-key check failed')
    finally:
        connection.close()


def snapshot_sqlite(source, destination, *, floor=FLOOR, timeout=180):
    before = plain_file(source)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    ensure_space(destination.parent, before.st_size * 2, floor)
    # mode=ro never creates or mutates the source database. WAL is read by SQLite.
    incoming = sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=2)
    outgoing = sqlite3.connect(destination)
    deadline = time.monotonic() + timeout
    try:
        incoming.execute('PRAGMA query_only=ON')
        def progress(status, remaining, total):
            if time.monotonic() >= deadline:
                raise transport.BackupError('online database snapshot timed out')
            ensure_space(destination.parent, CHUNK, floor)
        incoming.backup(outgoing, pages=128, progress=progress, sleep=0.02)
        outgoing.execute('PRAGMA journal_mode=DELETE')
    finally:
        outgoing.close(); incoming.close()
    os.chmod(destination, 0o600)
    after = plain_file(source)
    if (after.st_dev, after.st_ino) != (before.st_dev, before.st_ino):
        raise transport.BackupError('database source was replaced during online backup')
    verify_sqlite(destination)
    sha, size = file_digest(destination)
    return {'sha256': sha, 'bytes': size, 'integrity_verified': True, 'foreign_keys_verified': True,
            'source_permissions':source_permissions(before)}


CONTAINER_SQLITE_SCRIPT = r'''
import os,sqlite3,stat,sys,tempfile,time
from pathlib import Path
source=Path(sys.argv[1]);limit=int(sys.argv[2]);info=source.lstat()
assert source.is_absolute() and stat.S_ISREG(info.st_mode) and not source.is_symlink() and info.st_size<=limit
with tempfile.TemporaryDirectory(prefix='zj-online-sqlite-',dir='/tmp') as temporary:
 target=Path(temporary)/'snapshot.db'
 incoming=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True,timeout=2)
 outgoing=sqlite3.connect(target);deadline=time.monotonic()+120
 try:
  incoming.execute('PRAGMA query_only=ON')
  def progress(status,remaining,total):
   if time.monotonic()>deadline:raise RuntimeError('snapshot deadline')
  incoming.backup(outgoing,pages=128,progress=progress,sleep=.02)
  outgoing.execute('PRAGMA journal_mode=DELETE')
  assert outgoing.execute('PRAGMA integrity_check').fetchall()==[('ok',)]
  assert outgoing.execute('PRAGMA foreign_key_check').fetchone() is None
 finally:outgoing.close();incoming.close()
 assert target.stat().st_size<=limit
 with target.open('rb') as handle:
  while block:=handle.read(1024*1024):sys.stdout.buffer.write(block)
'''


def snapshot_container_sqlite(container, identity, original_path, destination, *, floor=FLOOR, runner=subprocess.run):
    """Snapshot in the source mount namespace; only an owned /tmp file is written.

    SQLite canonicalizes /proc/PID/root magic links to the wrong root in some
    containerd layouts. The fixed stdlib-only program avoids that ambiguity.
    Binary DB bytes go directly to the private host staging file, never stdout.
    """
    source=Path('/proc')/str(identity['pid'])/'root'/original_path.lstrip('/')
    before=plain_file(source)
    maximum=64*1024**2
    if before.st_size>maximum:raise transport.BackupError('container SQLite exceeds reviewed online snapshot bound')
    destination.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    ensure_space(destination.parent,maximum,floor)
    with destination.open('xb') as output:
        os.chmod(destination,0o600)
        result=runner(['docker','exec',container,'python','-I','-B','-c',CONTAINER_SQLITE_SCRIPT,original_path,str(maximum)],
                      stdout=output,stderr=subprocess.PIPE,timeout=150)
        output.flush();os.fsync(output.fileno())
    if result.returncode:raise transport.BackupError('container online SQLite snapshot failed')
    after=plain_file(source)
    if (before.st_dev,before.st_ino)!=(after.st_dev,after.st_ino):
        raise transport.BackupError('container SQLite source was replaced during snapshot')
    verify_sqlite(destination);sha,size=file_digest(destination)
    return {'sha256':sha,'bytes':size,'integrity_verified':True,'foreign_keys_verified':True,'source_permissions':source_permissions(before)}


def tree_files(root):
    if root.is_symlink() or not root.is_dir():
        raise transport.BackupError('managed data root is invalid')
    files = []
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in dirs:
            if (Path(directory) / name).is_symlink():
                raise transport.BackupError('managed data contains symlinks')
        for name in names:
            path = Path(directory) / name; plain_file(path)
            files.append(path)
            if len(files) > MAX_FILES:
                raise transport.BackupError('managed data exceeds file bound')
    return sorted(files)


def is_sqlite(path):
    with path.open('rb') as handle:
        return handle.read(16) == b'SQLite format 3\x00'


def database_references(path):
    """Read file metadata only, with bounded results, from the isolated snapshot."""
    refs = []
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute('PRAGMA query_only=ON')
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'stored_files' in tables:
            cols = {r[1] for r in db.execute('PRAGMA table_info(stored_files)')}
            required = {'storage_key', 'storage_backend', 'deletion_state', 'size', 'sha256'}
            if not required <= cols:
                raise transport.BackupError('stored file metadata schema is unsupported')
            query = "SELECT storage_key,storage_backend,size,sha256 FROM stored_files WHERE deletion_state NOT IN ('deleted','pending','uploading') LIMIT ?"
            rows = db.execute(query, (MAX_FILES + 1,)).fetchall()
            if len(rows) > MAX_FILES:
                raise transport.BackupError('file reference bound exceeded')
            for row in rows:
                if row['storage_backend'] not in {'local', 'oss-gateway'}:
                    raise transport.BackupError('unknown file reference backend')
                sha = row['sha256']
                if not transport.SHA.fullmatch(str(sha)) or type(row['size']) is not int or row['size'] < 0:
                    raise transport.BackupError('file reference integrity metadata is invalid')
                refs.append({'key': relative_key(row['storage_key']), 'backend': row['storage_backend'], 'bytes': row['size'], 'sha256': sha})
        # Legacy modules record oss://<relative-key>, never a bucket URL. Match
        # only explicit file-reference columns; do not scan user text/JSON bodies.
        for table in sorted(tables):
            if not SQL_NAME.fullmatch(table) or table == 'stored_files': continue
            columns = [r[1] for r in db.execute('PRAGMA table_info("' + table + '")')]
            candidates = [c for c in columns if SQL_NAME.fullmatch(c) and (c in {'object_ref','stored_name','measurement_method_image','product_image_ref'} or c.endswith('_object_ref'))]
            for column in candidates:
                where = ' AND deletion_state=\'active\'' if table == 'file_storage_uploads' and 'deletion_state' in columns else ''
                rows = db.execute(f'SELECT DISTINCT "{column}" FROM "{table}" WHERE substr("{column}",1,6)=\'oss://\'{where} LIMIT ?', (MAX_FILES + 1,)).fetchall()
                if len(rows) > MAX_FILES: raise transport.BackupError('file reference bound exceeded')
                refs.extend({'key': relative_key(r[0][6:]), 'backend': 'oss-gateway', 'bytes': None, 'sha256': None} for r in rows)
        unique = {}
        for ref in refs:
            key = (ref['backend'], ref['key'])
            if key in unique and any(unique[key][f] is not None and ref[f] is not None and unique[key][f] != ref[f] for f in ['bytes','sha256']):
                raise transport.BackupError('conflicting file reference metadata')
            if key not in unique or ref['sha256'] is not None: unique[key] = ref
        return sorted(unique.values(), key=lambda x: (x['backend'], x['key']))
    finally:
        db.close()


def verify_references(refs, files):
    for ref in refs:
        member = ('oss/' if ref['backend'] == 'oss-gateway' else 'data/files/') + ref['key']
        found = files.get(member)
        if found is None or any(ref[f] is not None and ref[f] != found[f] for f in ['bytes','sha256']):
            raise transport.BackupError('database file reference is missing or does not match captured bytes')


class ReadonlyObjects:
    """Only list/head/get methods exist; identity comes from the existing gateway."""
    def __init__(self, profile, slug):
        import oss2
        storage = profile.get('objectStorage') or {}
        if storage.get('provider') != 'aliyun-oss' or storage.get('mode') != 'gateway-api-v1':
            raise transport.BackupError('existing object storage identity is unsupported')
        path = Path(storage.get('credentialRef', '/etc/zhuojian/oss-gateway.env'))
        transport.private_file(path)
        values = {}
        for line in path.read_text().splitlines():
            if not line.strip() or line.lstrip().startswith('#'): continue
            key, sep, value = line.partition('=')
            if not sep or key.strip() in values: raise transport.BackupError('invalid protected source identity')
            values[key.strip()] = value.strip().strip('\"\'')
        endpoint = values.get('OSS_ENDPOINT', ''); parsed = urlsplit(endpoint)
        region = storage.get('region', '')
        if parsed.scheme != 'https' or parsed.hostname not in {f'oss-{region}.aliyuncs.com', f'oss-{region}-internal.aliyuncs.com'} or parsed.username or parsed.password or parsed.port not in {None,443} or parsed.path not in {'','/'} or parsed.query or parsed.fragment:
            raise transport.BackupError('source endpoint differs from registered region')
        if values.get('OSS_BUCKET') != storage.get('bucket'):
            raise transport.BackupError('source identity differs from registered bucket')
        prefix = relative_key(storage.get('rootPrefix', ''))
        expected = f"enterprises/{profile['organizationId']}/{profile['environment']}/apps"
        if prefix not in {'apps', expected}: raise transport.BackupError('unsupported object namespace')
        self.prefix = prefix + '/' + transport.valid_slug(slug) + '/'
        auth = oss2.StsAuth(values['OSS_ACCESS_KEY_ID'], values['OSS_ACCESS_KEY_SECRET'], values['OSS_SECURITY_TOKEN']) if values.get('OSS_SECURITY_TOKEN') else oss2.Auth(values['OSS_ACCESS_KEY_ID'], values['OSS_ACCESS_KEY_SECRET'])
        self.bucket = oss2.Bucket(auth, endpoint, storage['bucket'], connect_timeout=30)
        self.sdk = oss2

    def inventory(self):
        result = {}
        for obj in self.sdk.ObjectIteratorV2(self.bucket, prefix=self.prefix):
            if not obj.key.startswith(self.prefix): raise transport.BackupError('object escaped application prefix')
            key = relative_key(obj.key[len(self.prefix):])
            result[key] = {'bytes': obj.size, 'etag': obj.etag}
            if len(result) > MAX_FILES: raise transport.BackupError('object inventory bound exceeded')
        return result

    def capture(self, key, expected, destination, *, floor=FLOOR):
        full = self.prefix + relative_key(key)
        before = self.bucket.head_object(full)
        if before.etag != expected['etag'] or before.content_length != expected['bytes']:
            raise transport.BackupError('object changed since inventory')
        version = before.headers.get('x-oss-version-id')
        params = {'versionId': version} if version and version != 'null' else None
        incoming = self.bucket.get_object(full, params=params, headers={'If-Match': before.etag})
        h = hashlib.sha256(); size = 0
        try:
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            ensure_space(destination.parent, expected['bytes'], floor)
            with destination.open('xb') as outgoing:
                os.chmod(destination, 0o600)
                while block := incoming.read(CHUNK):
                    ensure_space(destination.parent, len(block), floor)
                    outgoing.write(block); h.update(block); size += len(block)
                outgoing.flush(); os.fsync(outgoing.fileno())
        finally: incoming.close()
        after = self.bucket.head_object(full)
        if size != expected['bytes'] or after.etag != before.etag or after.content_length != before.content_length:
            raise transport.BackupError('object changed during capture')
        return {'sha256': h.hexdigest(), 'bytes': size, 'source_version': version, 'source_etag': before.etag}


def container_identity(release, profile):
    name = release['containerName']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', name): raise transport.BackupError('invalid managed container name')
    template = '{"id":{{json .Id}},"pid":{{.State.Pid}},"running":{{.State.Running}},"image":{{json .Config.Image}},"owner":{{json (index .Config.Labels "com.zhuojian.managed-by")}},"app":{{json (index .Config.Labels "com.zhuojian.application")}},"enterprise":{{json (index .Config.Labels "com.zhuojian.enterprise")}},"commit":{{json (index .Config.Labels "com.zhuojian.commit")}}}'
    value = json.loads(run(['docker','inspect','--format',template,name]))
    if not value['running'] or value['pid'] <= 0 or value['owner'] != MANAGED_BY or value['app'] != release['applicationSlug'] or value['enterprise'] != profile['enterpriseKey'] or value['commit'] != release['current']['commit'] or value['image'] != release['current']['image']:
        raise transport.BackupError('running container differs from registered immutable release')
    return value


def verify_contents(root, manifest):
    files = manifest.get('files')
    if not isinstance(files, dict) or len(files) > MAX_FILES: raise transport.BackupError('invalid recovery file manifest')
    actual={p.relative_to(root).as_posix() for p in tree_files(root)}-{'manifest/recovery.json'}
    if actual!=set(files):raise transport.BackupError('isolated recovery member set differs from manifest')
    for member, expected in files.items():
        path = root / relative_key(member)
        if file_digest(path) != (expected['sha256'], expected['bytes']):
            raise transport.BackupError('isolated recovery member hash mismatch')
    for database in manifest['databases']:
        verify_sqlite(root / relative_key(database['member']))
    verify_references(manifest['references'], files)
    release=json.loads((root/'config/release.json').read_text()) if (root/'config/release.json').is_file() else None
    if release is not None and (release.get('applicationSlug')!=manifest.get('application_slug') or release.get('current',{}).get('commit')!=manifest.get('source_commit')):
        raise transport.BackupError('isolated release configuration does not match captured identity')
    for member,target in manifest.get('configuration_targets',{}).items():
        if target=='/etc/zhuojian/runtime.json':
            runtime=json.loads((root/relative_key(member)).read_text())
            if any(runtime.get(a)!=manifest.get(b) for a,b in [('organizationId','organization_id'),('runtimeId','runtime_id'),('environment','environment')]):
                raise transport.BackupError('isolated Runtime configuration identity differs')
    return {'database_integrity': True, 'file_hashes': True, 'reference_integrity': True}


def capture_one(profile, slug, app_plan, *, objects=None, runtime_helper=None, floor=FLOOR):
    """Create one validated online point, without writing the release or source data."""
    slug = transport.valid_slug(slug)
    deployment = profile.get('deployment') or {}
    releases = Path(deployment.get('deploymentsRoot', '/srv/zhuojian/deployments'))
    backups = Path(deployment.get('backupsRoot', '/srv/zhuojian/backups'))
    release_path = releases / slug / 'release.json'
    release = transport.read_json(release_path, allow_metadata_read=True)
    original_release = release_path.read_bytes()
    if release.get('applicationSlug') != slug or release.get('managedBy') != MANAGED_BY or release.get('backupMaintenance') or release.get('releaseSwitch'):
        raise transport.BackupError('application release is not ready for online capture')
    identity = container_identity(release, profile)
    commit = release['current']['commit']
    if not re.fullmatch(r'[a-f0-9]{40}', commit): raise transport.BackupError('invalid running source commit')
    destination = backups / slug
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    if destination.is_symlink(): raise transport.BackupError('backup root cannot be a symlink')
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    archive = destination / f'{stamp}-{commit[:12]}.tar.gz'
    captured_at = utc_now()
    if profile.get('objectStorage') and objects is None: objects = ReadonlyObjects(profile, slug)
    inventory = objects.inventory() if objects is not None else {}
    data_root = Path(release['dataDir'])
    local_files = tree_files(data_root)
    estimated = sum(p.stat().st_size for p in local_files) + sum(p['bytes'] for p in inventory.values())
    ensure_space(destination, estimated * 3 + 64 * 1024**2, floor)
    temporary = Path(tempfile.mkdtemp(prefix='.online-', dir=destination))
    os.chmod(temporary, 0o700)
    try:
        root = temporary / 'contents'; root.mkdir(mode=0o700)
        (root/'config').mkdir(mode=0o700); (root/'code').mkdir(mode=0o700)
        files = {}; databases = []; references = []; configuration_targets={}
        primary_path = app_plan.get('primary_sqlite')
        if not isinstance(primary_path, str) or not PurePosixPath(primary_path).is_absolute() or '..' in PurePosixPath(primary_path).parts:
            raise transport.BackupError('reviewed primary SQLite location is required')
        primary_member = None
        for source in local_files:
            relative = source.relative_to(data_root).as_posix()
            if source.name.endswith(('-wal','-shm','-journal')): continue
            member = 'data/' + relative_key(relative); target = root/member; target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            if is_sqlite(source):
                files[member] = snapshot_sqlite(source, target, floor=floor)
                is_primary = '/data/' + relative == primary_path
                databases.append({'member': member, 'primary': is_primary, 'restore_target': '/data/' + relative})
                if is_primary: primary_member = member
            else: files[member] = copy_stable(source, target, floor=floor)
        if primary_member is None:
            # A known legacy app may keep SQLite in its container writable layer.
            # Pin the current PID; do not import the app or change its mounts.
            source = Path('/proc')/str(identity['pid'])/'root'/primary_path.lstrip('/')
            member = 'container-data/' + relative_key(primary_path.lstrip('/'))
            target = root/member; target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            files[member] = snapshot_container_sqlite(release['containerName'],identity,primary_path,target,floor=floor)
            databases.append({'member': member, 'primary': True, 'restore_target': primary_path})
            primary_member = member
        references = database_references(root/primary_member)
        for key, expected in inventory.items():
            member = 'oss/' + relative_key(key)
            files[member] = objects.capture(key, expected, root/member, floor=floor)
        if objects is not None and objects.inventory() != inventory:
            raise transport.BackupError('object inventory changed during capture; retry this application')
        for name, source in [('app.env', release['envFile']), ('release.json', release_path), ('nginx.conf', release.get('nginxConfig'))]:
            if source is None or (name == 'nginx.conf' and not Path(source).exists()): continue
            files['config/' + name] = copy_stable(Path(source), root/'config'/name, floor=floor)
            configuration_targets['config/'+name]=str(source)
        if release.get('storageEnvFile'):
            transport.private_file(Path(release['storageEnvFile']))
            files['config/storage.env']=copy_stable(Path(release['storageEnvFile']),root/'config/storage.env',floor=floor)
            configuration_targets['config/storage.env']=release['storageEnvFile']
        # A reviewed plan may include same-enterprise host identity/registry
        # configuration needed to reconstruct the app on a fresh host. Values
        # stay only in this private archive; the public projection gets counts.
        host_files=app_plan.get('private_host_files',{})
        if not isinstance(host_files,dict) or len(host_files)>30:
            raise transport.BackupError('host recovery configuration plan is invalid')
        for name,source_name in host_files.items():
            name=relative_key(name);source_path=Path(source_name)
            if not source_path.is_absolute() or '..' in source_path.parts or not str(source_path).startswith(('/etc/zhuojian/','/usr/local/lib/zhuojian/','/var/lib/zhuojian-storage-gateway/')):
                raise transport.BackupError('host recovery configuration path is outside approved roots')
            member='config/host/'+name;target=root/member;target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            if is_sqlite(source_path):
                files[member]=snapshot_sqlite(source_path,target,floor=floor)
                databases.append({'member':member,'primary':False,'restore_target':str(source_path),'host_configuration':True})
            else:files[member]=copy_stable(source_path,target,floor=floor)
            configuration_targets[member]=str(source_path)
        if os.name=='posix' and app_plan.get('capture_container_layout',True):
            layout_template='{"image_id":{{json .Image}},"image_reference":{{json .Config.Image}},"user":{{json .Config.User}},"working_dir":{{json .Config.WorkingDir}},"entrypoint":{{json .Config.Entrypoint}},"command":{{json .Config.Cmd}},"mounts":{{json .Mounts}},"networks":{{json .NetworkSettings.Networks}},"port_bindings":{{json .HostConfig.PortBindings}},"restart_policy":{{json .HostConfig.RestartPolicy}}}'
            layout=json.loads(run(['docker','inspect','--format',layout_template,release['containerName']]))
            transport.atomic_json(root/'config/container-layout.json',layout)
            sha,size=file_digest(root/'config/container-layout.json');files['config/container-layout.json']={'sha256':sha,'bytes':size}
        if runtime_helper is None: raise transport.BackupError('verified Runtime source helper is required')
        source_proof = runtime_helper.backup_git_repository(Path(release['projectDir']), commit, root/'code/repository.bundle')
        sha, size = file_digest(root/'code/repository.bundle'); files['code/repository.bundle'] = {'sha256':sha, 'bytes':size}
        if release_path.read_bytes() != original_release or container_identity(release, profile) != identity:
            raise transport.BackupError('running release changed during online capture')
        verify_references(references, files)
        manifest = {'schema_version':1,'producer':MARKER,'organization_id':profile['organizationId'],'runtime_id':profile['runtimeId'],
                    'environment':profile['environment'],'application_slug':slug,'captured_at':captured_at,'source_commit':commit,
                    'files':files,'databases':databases,'references':references,'source':source_proof,
                    'configuration_targets':configuration_targets,
                    'data_root_permissions':source_permissions(data_root.stat()),
                    'oss_inventory_checked':objects is not None,'oss_object_count':len(inventory),'oss_object_bytes':sum(p['bytes'] for p in inventory.values()),
                    'limitations':['per_database_consistency','not_cross_database_atomic','external_sources_excluded','post_point_writes_excluded']}
        verify_contents(root, manifest)
        (root/'manifest').mkdir(mode=0o700)
        transport.atomic_json(root/'manifest/recovery.json', manifest)
        manifest_sha, _ = file_digest(root/'manifest/recovery.json')
        temp_archive = temporary/'point.tar.gz'
        with tarfile.open(temp_archive,'w:gz',format=tarfile.PAX_FORMAT) as handle:
            for path in sorted(root.iterdir()): handle.add(path,arcname=path.name,recursive=True)
        os.chmod(temp_archive,0o600)
        # Full compressed stream readback, plus hashes in its private manifest.
        with tarfile.open(temp_archive,'r:gz') as handle:
            for member in handle:
                if member.isfile():
                    h=hashlib.sha256(); count=0
                    with handle.extractfile(member) as incoming:
                        while block:=incoming.read(CHUNK):h.update(block);count+=len(block)
                    expected=files.get(member.name)
                    if count!=member.size or (expected and (h.hexdigest(),count)!=(expected['sha256'],expected['bytes'])):
                        raise transport.BackupError('archive member readback failed')
        sha,size=file_digest(temp_archive)
        metadata={'schemaVersion':3,'managedBy':MANAGED_BY,'applicationSlug':slug,'createdAt':utc_now(),'capturedAt':captured_at,
                  'commit':commit,'archive':archive.name,'sha256':sha,'sizeBytes':size,'consistentOfflineSnapshot':False,
                  'consistency':{'method':'sqlite_online_backup','databaseIntegrityVerified':True,'fileHashesVerified':True,
                                 'referencesVerified':True,'businessServicesStopped':False,'manifestSha256':manifest_sha},
                  'source':source_proof,'offServer':False}
        primary_members={d['member'] for d in databases if d['primary']}
        db_members={d['member'] for d in databases}
        def component(members,included=True):
            return {'included':included,'verified':True if included else None,'count':len(members) if included else 0,
                    'bytes':sum(files[n]['bytes'] for n in members) if included else 0}
        metadata['components']={'database':component(primary_members),
            'local_files':component([n for n in files if n.startswith('data/') and n not in db_members]),
            'oss_files':component([n for n in files if n.startswith('oss/')],objects is not None),
            'code':component(['code/repository.bundle']),'config':component([n for n in files if n.startswith('config/')])}
        metadata['limitations']=manifest['limitations']+['runtime_services_not_started','image_bytes_not_exported']
        os.replace(temp_archive,archive)
        transport.atomic_json(archive.with_suffix(archive.suffix+'.json'),metadata)
        return {'applicationSlug':slug,'archive':str(archive),'sha256':sha,'sizeBytes':size,'capturedAt':captured_at,'offServer':False}
    finally:
        # Only this invocation's checked private staging directory is removed.
        if temporary.parent.resolve()!=destination.resolve() or not temporary.name.startswith('.online-') or temporary.is_symlink():
            raise transport.BackupError('unsafe online staging cleanup target')
        shutil.rmtree(temporary)


def load_runtime_helper(path):
    if path.is_symlink() or not path.is_file():raise transport.BackupError('Runtime helper is unavailable')
    spec=importlib.util.spec_from_file_location('zhuojian_backup_runtime_helper',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime-profile',type=Path,default=Path('/etc/zhuojian/runtime.json'))
    p.add_argument('--plan',type=Path,default=Path('/etc/zhuojian/backup-online-plan.json'))
    p.add_argument('--runtime-helper',type=Path,default=Path('/usr/local/lib/zhuojian/runtime_admin.py'))
    p.add_argument('--publish',action='store_true')
    p.add_argument('--verify-restore',action='store_true')
    p.add_argument('application_slug',nargs='?',default='all')
    args=p.parse_args(argv)
    try:
        if os.name!='posix' or os.geteuid()!=0:raise transport.BackupError('online backup requires Runtime root')
        profile=transport.read_json(args.runtime_profile,allow_metadata_read=True); plan=transport.read_json(args.plan)
        for key in ['organizationId','runtimeId','environment']:
            if plan.get(key)!=profile.get(key):raise transport.BackupError('online plan belongs to another Runtime')
        applications=plan.get('applications')
        if not isinstance(applications,dict) or not applications:raise transport.BackupError('online plan has no reviewed applications')
        if args.application_slug=='all':
            registered=set()
            releases=Path(profile.get('deployment',{}).get('deploymentsRoot','/srv/zhuojian/deployments'))
            for path in releases.glob('*/release.json'):
                value=transport.read_json(path,allow_metadata_read=True)
                if value.get('managedBy')==MANAGED_BY:registered.add(value.get('applicationSlug'))
            if registered!=set(applications):raise transport.BackupError('online plan does not cover current registered applications')
        selected=sorted(applications) if args.application_slug=='all' else [transport.valid_slug(args.application_slug)]
        helper=load_runtime_helper(args.runtime_helper)
        result={'ok':True,'backups':[],'failed':[]}
        scope=transport.BackupScope(profile) if args.publish else None
        backend=transport.OssBackend(scope) if scope is not None else None
        if backend is not None:backend.assert_scope(scope);backend.require_versioning()
        if args.verify_restore and backend is None:raise transport.BackupError('isolated remote restore requires publication')
        with transport.publication_lock(Path('/run/lock/zhuojian-runtime-admin.lock')):
            for slug in selected:
                transport.valid_slug(slug)
                backup_dir=Path(profile.get('deployment',{}).get('backupsRoot','/srv/zhuojian/backups'))/slug
                job={'status':'running','attempt_at':utc_now(),'finished_at':None,'error_code':None,'phase':'capture','archive':None}
                transport.atomic_json(backup_dir/'online-job.json',job)
                stage=None
                try:
                    with transport.publication_lock(Path('/run/lock/zhuojian-online-backup.lock')):
                        point=capture_one(profile,slug,applications[slug],runtime_helper=helper)
                        archive=Path(point['archive']);job['archive']=archive.name
                        if backend is not None:
                            job['phase']='offsite';transport.atomic_json(backup_dir/'online-job.json',job)
                            remote=transport.publish(scope,backend,slug,archive)
                            point['offServer']=True
                            if args.verify_restore:
                                job['phase']='restore';transport.atomic_json(backup_dir/'online-job.json',job)
                                checks=Path('/srv/zhuojian/restore-checks/online')/slug
                                checks.mkdir(parents=True,exist_ok=True,mode=0o700)
                                ensure_space(checks,archive.stat().st_size*3)
                                stage=checks/archive.name.removesuffix('.tar.gz')
                                restored=transport.stage_restore(scope,backend,slug,archive.name,stage)
                                restored.update(archiveName=archive.name,sha256=remote['sha256'],versionId=remote['versionId'])
                                transport.atomic_json(archive.with_suffix(archive.suffix+'.restore.json'),restored)
                                point['restoreVerified']=True
                        result['backups'].append(point)
                    job.update(status='success',finished_at=utc_now(),phase='completed')
                except Exception:
                    code={'capture':'online_backup_failed','offsite':'offsite_failed','restore':'restore_failed'}.get(job['phase'],'backup_failed')
                    job.update(status='failed',finished_at=utc_now(),error_code=code)
                    result['failed'].append({'applicationSlug':slug,'error_code':code,'localPreserved':True})
                finally:
                    transport.atomic_json(backup_dir/'online-job.json',job)
                    if job['status']=='success' and stage is not None and stage.is_dir() and not stage.is_symlink() and stage.parent==Path('/srv/zhuojian/restore-checks/online')/slug:
                        # Retain receipts above; remove only this owned, isolated
                        # validation tree so daily restore does not fill the host.
                        shutil.rmtree(stage)
        result['ok']=not result['failed'];print(json.dumps(result,sort_keys=True));return 0 if result['ok'] else 2
    except Exception:
        print(json.dumps({'ok':False,'error_code':'online_backup_failed','localPreserved':True}),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
