import hashlib
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
import runtime_backup_oss as transport
from test_runtime_backup_oss import Backend,profile,source


def seed(tmp_path,backend,hour,schema=3,restore=True):
    scope=transport.BackupScope(profile(tmp_path));name=f'20261027T{hour:02d}0000Z-bbbbbbbbbbbb.tar.gz'
    path=scope.backups/'example'/name;path.parent.mkdir(parents=True,exist_ok=True);data=f'archive-{hour}'.encode();path.write_bytes(data);path.chmod(0o600)
    sha=hashlib.sha256(data).hexdigest();size=len(data)
    transport.atomic_json(path.with_suffix('.gz.json'),{'schemaVersion':schema,'sha256':sha,'sizeBytes':size})
    remote={'schemaVersion':1,'organizationId':scope.organization,'environment':scope.environment,'runtimeId':scope.runtime,'applicationSlug':'example',
            'bucket':scope.bucket,'archive':name,'objectKey':scope.archive_key('example',name),'versionId':'version-1','sha256':sha,'sizeBytes':size,'commit':'b'*40,'source':source(),'status':'verified'}
    transport.atomic_json(path.with_suffix('.gz.remote.json'),remote);backend.objects[remote['objectKey']]=data
    if restore:
        transport.atomic_json(path.with_suffix('.gz.restore.json'),{'archiveName':name,'sha256':sha,'versionId':'version-1','businessDatabaseVerified':True,'gitVerified':True,
            'fileHashesVerified':True,'referenceIntegrityVerified':True,'referencesRequeried':True})
    return scope,path


def test_retention_keeps_two_verified_v3_and_all_legacy_with_thin_receipts(tmp_path):
    backend=Backend();_,legacy=seed(tmp_path,backend,7,schema=2)
    points=[seed(tmp_path,backend,h)[1] for h in [8,9,10]];scope=transport.BackupScope(profile(tmp_path))
    plan=transport.prune_online_local(scope,backend,'example',keep=2)
    assert plan['eligible']==[points[0].name] and all(p.exists() for p in points)
    result=transport.prune_online_local(scope,backend,'example',keep=2,apply=True)
    assert [p.exists() for p in points]==[False,True,True] and legacy.exists()
    assert points[0].with_suffix('.gz.json').exists() and points[0].with_suffix('.gz.remote.json').exists() and points[0].with_suffix('.gz.restore.json').exists()
    assert len(result['deleted'])==1 and len(backend.objects)==4


def test_corrupt_remote_or_unverified_restore_preserves_local_bytes(tmp_path):
    backend=Backend();scope,old=seed(tmp_path,backend,7,restore=False)
    points=[seed(tmp_path,backend,h)[1] for h in [8,9,10]];backend.corrupt=True
    result=transport.prune_online_local(scope,backend,'example',keep=2,apply=True)
    assert not result['deleted'] and old.exists() and all(p.exists() for p in points)
