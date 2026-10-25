import hashlib
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
from types import SimpleNamespace

import pytest


SPEC = importlib.util.spec_from_file_location('runtime_backup_oss', Path(__file__).parents[1] / 'scripts/runtime_backup_oss.py')
b = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(b)
ORG = '65130a23-b05e-4026-9615-761ab2d4193c'
NAME = '20261025T090000Z-123456789abc.tar.gz'


def profile(tmp_path):
    return {'organizationId': ORG, 'environment': 'staging', 'runtimeId': 'example-runtime',
            'backupStorage': {'provider': 'aliyun-oss', 'namespaceMode': 'enterprise-v1',
                              'bucket': 'shared-backups', 'region': 'cn-hangzhou',
                              'rootPrefix': f'enterprises/{ORG}/staging/backups'},
            'deployment': {'backupsRoot': str(tmp_path / 'backups'), 'deploymentsRoot': str(tmp_path / 'deployments')}}


def source():
    return {'restoreVerified': True, 'bundleMember': 'code/repository.bundle',
            'bundleSha256': 'a' * 64, 'headCommit': 'b' * 40,
            'requiredReleaseCommit': 'b' * 40, 'uncommittedStateIncluded': False}


def local_archive(tmp_path, data=b'archive', git_source=None):
    scope = b.BackupScope(profile(tmp_path))
    path = scope.backups / 'example' / NAME
    path.parent.mkdir(parents=True)
    path.write_bytes(data)
    path.chmod(0o600)
    meta = {'managedBy': b.MANAGED_BY, 'applicationSlug': 'example', 'archive': NAME,
            'schemaVersion': 2, 'consistentOfflineSnapshot': True, 'source': git_source or source(),
            'sha256': hashlib.sha256(data).hexdigest(), 'sizeBytes': len(data),
            'commit': (git_source or source())['requiredReleaseCommit'],
            'createdAt': '2026-10-25T09:00:00Z'}
    b.atomic_json(path.with_suffix('.gz.json'), meta)
    return scope, path


class Backend:
    def __init__(self):
        self.objects = {}
        self.manifests = {}
        self.gets = []
        self.uploads = 0
        self.corrupt = False
        self.unknown_manifest = False

    def require_versioning(self):
        pass

    def assert_private(self,key,version_id):
        assert key in self.objects
        assert version_id=='version-1'

    def head(self, key):
        if key in self.objects:
            return {'versionId': 'version-1', 'size': len(self.objects[key])}

    def manifest(self, key):
        return self.manifests.get(key)

    def upload(self, key, path, size, sha, journal):
        self.uploads += 1
        self.objects[key] = path.read_bytes()
        return self.head(key)

    def put_manifest(self, key, value):
        self.manifests[key] = value
        if self.unknown_manifest:
            raise TimeoutError('lost response')
        return 'manifest-version-1'

    def get(self, key, version_id=None):
        self.gets.append((key, version_id))
        return io.BytesIO(b'corrupted' if self.corrupt else self.objects[key])

    def list_manifest_keys(self, prefix):
        return (key for key in self.manifests if key.startswith(prefix))


def test_scope_is_derived_and_rejects_other_enterprise(tmp_path):
    p = profile(tmp_path)
    scope = b.BackupScope(p)
    assert scope.archive_key('example', NAME).startswith(f'enterprises/{ORG}/staging/backups/applications/example/')
    with pytest.raises(b.BackupError):
        scope.archive_key('../other', NAME)
    p['backupStorage']['rootPrefix'] = 'enterprises/other/staging/backups'
    with pytest.raises(b.BackupError):
        b.BackupScope(p)


def test_publish_verifies_exact_version_and_replays_without_upload(tmp_path):
    scope, path = local_archive(tmp_path)
    remote = Backend()
    result = b.publish(scope, remote, 'example', path)
    assert result['offServer'] is True
    assert result['status'] == 'verified'
    assert remote.gets == [(scope.archive_key('example', NAME), 'version-1')]
    assert b.read_json(path.with_suffix('.gz.remote.json'))['sha256'] == result['sha256']
    assert b.publish(scope, remote, 'example', path)['reused'] is True
    assert remote.uploads == 1
    assert len(b.discover(scope, remote, 'example')) == 1


def test_corrupt_remote_never_creates_receipt_or_manifest(tmp_path):
    scope, path = local_archive(tmp_path)
    remote = Backend()
    remote.corrupt = True
    with pytest.raises(b.BackupError):
        b.publish(scope, remote, 'example', path)
    assert not remote.manifests
    assert not path.with_suffix('.gz.remote.json').exists()
    assert path.read_bytes() == b'archive'


def test_unknown_manifest_write_is_read_back_not_resubmitted(tmp_path):
    scope, path = local_archive(tmp_path)
    remote = Backend()
    remote.unknown_manifest = True
    assert b.publish(scope, remote, 'example', path)['status'] == 'verified'
    assert remote.uploads == 1


@pytest.mark.parametrize('change', ['sha', 'git', 'company'])
def test_invalid_local_or_remote_proof_refuses(tmp_path, change):
    scope, path = local_archive(tmp_path)
    remote = Backend()
    if change == 'company':
        result = b.publish(scope, remote, 'example', path)
        remote.manifests[scope.manifest_key('example', NAME)] = {**result, 'organizationId': 'other'}
        expected_uploads = 1
    else:
        sidecar = path.with_suffix('.gz.json')
        meta = b.read_json(sidecar)
        if change == 'sha':
            meta['sha256'] = 'c' * 64
        else:
            meta['source']['requiredReleaseCommit'] = 'not-a-commit'
        b.atomic_json(sidecar, meta)
        expected_uploads = 0
    with pytest.raises(b.BackupError):
        b.publish(scope, remote, 'example', path)
    assert remote.uploads == expected_uploads


class MultipartBucket:
    def __init__(self):
        self.parts = []
        self.inits = 0
        self.completes = 0
        self.listed_parts = 0

    def init_multipart_upload(self, *args, **kwargs):
        self.inits += 1
        return SimpleNamespace(upload_id='upload-1')

    def upload_part(self, key, upload_id, number, data):
        assert upload_id == 'upload-1'
        self.parts.append((number, len(data), hashlib.sha256(data).hexdigest()))
        return SimpleNamespace(etag=f'etag-{number}')

    def complete_multipart_upload(self, key, upload_id, parts):
        self.completes += 1
        return SimpleNamespace(headers={'x-oss-version-id': 'large-version'})

    def list_parts(self, *args, **kwargs):
        self.listed_parts += 1
        return SimpleNamespace()


def multipart_backend(candidates=()):
    backend = b.OssBackend.__new__(b.OssBackend)
    backend.bucket = MultipartBucket()
    backend.sdk = SimpleNamespace(models=SimpleNamespace(PartInfo=lambda number, etag: (number, etag)),
                                  MultipartUploadIterator=lambda *args, **kwargs: iter(candidates))
    return backend


def test_multipart_archive_larger_than_gateway_limit_uses_bounded_parts(tmp_path):
    path = tmp_path / 'large.tar.gz'
    size = 513 * 1024 * 1024
    with path.open('wb') as handle:
        handle.truncate(size)
    backend = multipart_backend()
    result = backend.upload('owned-key', path, size, 'a' * 64, tmp_path / 'journal.json')
    assert result == {'versionId': 'large-version', 'size': size}
    assert sum(part[1] for part in backend.bucket.parts) == size
    assert max(part[1] for part in backend.bucket.parts) == b.CHUNK
    assert len(backend.bucket.parts) == 65
    assert backend.bucket.inits == backend.bucket.completes == 1


@pytest.mark.parametrize('phase', ['uploading', 'completing'])
def test_unknown_multipart_write_resumes_only_existing_operation(tmp_path, phase):
    path = tmp_path / 'small.tar.gz'
    path.write_bytes(b'recoverable')
    state = {'objectKey': 'owned-key', 'sha256': 'a' * 64, 'sizeBytes': 11, 'phase': phase}
    state['uploadId'] = 'upload-1'
    journal = tmp_path / 'journal.json'
    b.atomic_json(journal, state)
    backend = multipart_backend([SimpleNamespace(key='owned-key', upload_id='upload-1')])
    backend.upload('owned-key', path, 11, 'a' * 64, journal)
    assert backend.bucket.inits == 0
    assert backend.bucket.completes == 1


def test_unknown_initiation_without_unique_match_never_restarts(tmp_path):
    journal = tmp_path / 'journal.json'
    b.atomic_json(journal, {'objectKey': 'key', 'sha256': 'a' * 64, 'sizeBytes': 1, 'phase': 'initiating'})
    backend = multipart_backend()
    with pytest.raises(b.BackupError):
        backend.upload('key', tmp_path / 'unused', 1, 'a' * 64, journal)
    assert backend.bucket.inits == 0


def make_bundle(tmp_path):
    repo = tmp_path / 'source'
    repo.mkdir()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL).decode().strip()
    git('init')
    (repo / 'business.txt').write_text('data')
    git('add', 'business.txt')
    git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'fixture')
    commit = git('rev-parse', 'HEAD')
    bundle = tmp_path / 'repository.bundle'
    git('bundle', 'create', str(bundle), '--all')
    return bundle, commit


def test_isolated_restore_verifies_real_git_without_touching_live_files(tmp_path):
    bundle, commit = make_bundle(tmp_path)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as archive:
        archive.add(bundle, arcname='code/repository.bundle')
        data = tarfile.TarInfo('data/business.txt')
        data.size = 4
        archive.addfile(data, io.BytesIO(b'data'))
    git_source = {**source(), 'headCommit': commit, 'requiredReleaseCommit': commit,
                  'bundleSha256': hashlib.sha256(bundle.read_bytes()).hexdigest()}
    scope, path = local_archive(tmp_path, buf.getvalue(), git_source)
    remote = Backend()
    b.publish(scope, remote, 'example', path)
    destination = tmp_path / 'restore'
    result = b.stage_restore(scope, remote, 'example', NAME, destination)
    assert result['gitVerified'] is True
    assert result['businessDatabaseVerified'] is False
    assert result['restoredToLive'] is False
    assert (destination / 'contents/data/business.txt').read_bytes() == b'data'
    assert path.exists()
    with pytest.raises(b.BackupError):
        b.download(scope, remote, 'example', NAME, destination)


@pytest.mark.parametrize('name', ['data/../../outside', '/data/absolute', 'data/link'])
def test_restore_rejects_traversal_and_links(tmp_path, name):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as archive:
        member = tarfile.TarInfo(name)
        if name == 'data/link':
            member.type = tarfile.SYMTYPE
            member.linkname = '/etc/passwd'
        archive.addfile(member)
    scope, path = local_archive(tmp_path, buf.getvalue())
    remote = Backend()
    b.publish(scope, remote, 'example', path)
    with pytest.raises(b.BackupError):
        b.stage_restore(scope, remote, 'example', NAME, tmp_path / 'restore')
    assert not (tmp_path / 'outside').exists()


def test_backup_scope_probe_rejects_broad_ram_even_without_real_data():
    backend = b.OssBackend.__new__(b.OssBackend)
    backend.bucket = SimpleNamespace(list_objects_v2=lambda **kwargs: [])
    with pytest.raises(b.BackupError, match='outside'):
        backend.assert_scope(b.BackupScope(profile(Path('/tmp/backup-test'))))


def test_backup_scope_probe_checks_all_negative_operations():
    operations = []
    def deny(name):
        def action(*args, **kwargs):
            operations.append((name, args, kwargs))
            error = RuntimeError('denied')
            error.status = 403
            raise error
        return action
    backend = b.OssBackend.__new__(b.OssBackend)
    backend.bucket = SimpleNamespace(**{name: deny(name) for name in ['list_objects_v2', 'head_object', 'delete_object', 'put_object']})
    backend.assert_scope(b.BackupScope(profile(Path('/tmp/backup-test'))))
    assert len(operations) == 12
    assert '/apps/' in operations[-1][1][0]


def test_retention_keeps_newest_and_requires_current_remote_readback(tmp_path):
    scope, path = local_archive(tmp_path)
    remote = Backend()
    b.publish(scope, remote, 'example', path)
    newer = []
    for day in ['26', '27']:
        item = path.with_name(NAME.replace('20261025', '202610' + day))
        item.write_bytes(b'newer local recovery point')
        item.chmod(0o600)
        newer.append(item)
    plan = b.prune_local(scope, remote, 'example', 2)
    assert plan['candidates'] == [NAME]
    assert path.exists()
    remote.corrupt = True
    assert b.prune_local(scope, remote, 'example', 2, True)['removed'] == []
    assert path.exists()
    remote.corrupt = False
    assert b.prune_local(scope, remote, 'example', 2, True)['removed'] == [NAME]
    assert not path.exists()
    assert path.with_suffix('.gz.remote.json').exists()
    assert all(item.exists() for item in newer)
    with pytest.raises(b.BackupError):
        b.prune_local(scope, remote, 'example', 1, True)


def test_public_backup_object_never_gets_verified_receipt(tmp_path):
    scope, path = local_archive(tmp_path)
    remote = Backend()
    def public(key, version_id):
        raise b.BackupError('backup object is anonymously readable')
    remote.assert_private = public
    with pytest.raises(b.BackupError, match='anonymously'):
        b.publish(scope, remote, 'example', path)
    assert not remote.manifests
    assert not path.with_suffix('.gz.remote.json').exists()


def test_configure_checks_cloud_boundary_before_atomic_profile_write(tmp_path,monkeypatch,capsys):
    p=profile(tmp_path)
    p.pop('backupStorage')
    p['untouched']={'meaning':'existing Runtime configuration'}
    path=tmp_path/'runtime.json'
    b.atomic_json(path,p)
    monkeypatch.setattr(b,'publication_lock',lambda _path:contextlib.nullcontext())
    class Cloud:
        def __init__(self,scope):self.scope=scope
        def assert_scope(self,scope):assert scope.organization==ORG
        def require_versioning(self):pass
    monkeypatch.setattr(b,'OssBackend',Cloud)
    args=['--runtime-profile',str(path),'configure','--bucket','shared-backups','--region','cn-hangzhou']
    assert b.main(args)==0
    configured=b.read_json(path)
    assert configured['untouched']==p['untouched']
    assert configured['backupStorage']['boundaryVerified'] is True
    assert json.loads(capsys.readouterr().out)['uploadVerified'] is False
    before=path.read_bytes()
    assert b.main([*args[:-3],'other-shared-backups','--region','cn-hangzhou'])==2
    assert path.read_bytes()==before


def test_configure_failed_boundary_keeps_existing_profile(tmp_path,monkeypatch):
    p=profile(tmp_path);p.pop('backupStorage')
    path=tmp_path/'runtime.json';b.atomic_json(path,p);before=path.read_bytes()
    monkeypatch.setattr(b,'publication_lock',lambda _path:contextlib.nullcontext())
    class Cloud:
        def __init__(self,scope):pass
        def assert_scope(self,scope):raise b.BackupError('boundary failed')
    monkeypatch.setattr(b,'OssBackend',Cloud)
    assert b.main(['--runtime-profile',str(path),'configure','--bucket','shared-backups','--region','cn-hangzhou'])==2
    assert path.read_bytes()==before


def test_current_runtime_fractional_timestamp_roundtrips_through_remote_discovery(tmp_path):
    scope, old_path = local_archive(tmp_path)
    metadata = b.read_json(old_path.with_suffix('.gz.json'))
    stamp = b.dt.datetime(2026, 10, 25, 9, 0, 0, 123456).strftime('%Y%m%dT%H%M%S.%fZ')
    name = f'{stamp}-{metadata["commit"][:12]}.tar.gz'
    path = old_path.with_name(name)
    old_path.rename(path)
    metadata['archive'] = name
    b.atomic_json(path.with_suffix('.gz.json'), metadata)
    remote = Backend()
    result = b.publish(scope, remote, 'example', path)
    assert result['archive'] == name
    assert b.discover(scope, remote, 'example')[0]['archive'] == name
    assert b.download(scope, remote, 'example', name, tmp_path / 'isolated')['status'] == 'downloaded_and_verified'


@pytest.mark.parametrize('change', [{'schemaVersion': 1}, {'schemaVersion': True}, {'commit': 'c' * 40}])
def test_local_backup_schema_and_running_source_must_match_before_upload(tmp_path, change):
    scope, path = local_archive(tmp_path)
    sidecar = path.with_suffix('.gz.json')
    b.atomic_json(sidecar, {**b.read_json(sidecar), **change})
    remote = Backend()
    with pytest.raises(b.BackupError):
        b.publish(scope, remote, 'example', path)
    assert remote.uploads == 0


def test_publish_latest_accepts_runtime_metadata_mode_and_continues_other_apps(tmp_path, monkeypatch, capsys):
    scope, path = local_archive(tmp_path)
    runtime_path = tmp_path / 'runtime.json'
    b.atomic_json(runtime_path, profile(tmp_path))
    good_release = scope.deployments / 'example' / 'release.json'
    b.atomic_json(good_release, {'managedBy': b.MANAGED_BY, 'applicationSlug': 'example'})
    good_release.chmod(0o640)
    bad_release = scope.deployments / 'broken' / 'release.json'
    b.atomic_json(bad_release, {'managedBy': b.MANAGED_BY, 'applicationSlug': 'wrong-app'})
    bad_release.chmod(0o640)
    remote = Backend()
    remote.assert_scope = lambda _scope: None
    monkeypatch.setattr(b, 'OssBackend', lambda _scope: remote)
    assert b.main(['--runtime-profile', str(runtime_path), 'publish-latest']) == 2
    result = json.loads(capsys.readouterr().out)
    assert [row['applicationSlug'] for row in result['backups']] == ['example']
    assert [row['applicationSlug'] for row in result['failed']] == ['broken']
    assert path.exists()


@pytest.mark.skipif(os.name != 'posix', reason='real POSIX metadata/credential permission distinction')
def test_readable_runtime_metadata_does_not_relax_private_backup_credentials(tmp_path):
    path = tmp_path / 'metadata.json'
    b.atomic_json(path, {'applicationSlug': 'example'})
    path.chmod(0o640)
    assert b.read_json(path, allow_group_read=True)['applicationSlug'] == 'example'
    with pytest.raises(b.BackupError):
        b.private_file(path)
    path.chmod(0o660)
    with pytest.raises(b.BackupError):
        b.read_json(path, allow_group_read=True)


def test_restore_checks_download_capacity_before_creating_partial_files(tmp_path, monkeypatch):
    scope, path = local_archive(tmp_path)
    remote = Backend()
    b.publish(scope, remote, 'example', path)
    monkeypatch.setattr(b.shutil, 'disk_usage', lambda _: SimpleNamespace(free=1))
    with pytest.raises(b.BackupError, match='disk space'):
        b.download(scope, remote, 'example', NAME, tmp_path / 'restore')
    assert not (tmp_path / 'restore').exists()
