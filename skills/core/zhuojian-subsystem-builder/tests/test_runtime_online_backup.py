import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys
import threading
from types import SimpleNamespace
import io

import pytest

SCRIPTS = Path(__file__).parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import runtime_online_backup as online
import runtime_backup_oss as transport


def sqlite_db(path, *, file_key=None, backend='local', data=b'document'):
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute('CREATE TABLE records(id INTEGER PRIMARY KEY, value TEXT)')
        connection.execute('INSERT INTO records(value) VALUES (?)', ('retained',))
        connection.execute('CREATE TABLE stored_files(storage_key TEXT,storage_backend TEXT,deletion_state TEXT,size INTEGER,sha256 TEXT)')
        if file_key:
            connection.execute('INSERT INTO stored_files VALUES (?,?,?,?,?)', (file_key,backend,'active',len(data),hashlib.sha256(data).hexdigest()))


def test_online_snapshot_includes_live_wal_without_stopping_writer(tmp_path):
    source=tmp_path/'live.db';target=tmp_path/'stage'/'recovery.db'
    sqlite_db(source)
    writer=sqlite3.connect(source,check_same_thread=False)
    writer.execute('PRAGMA journal_mode=WAL')
    writer.execute("INSERT INTO records(value) VALUES ('committed-in-wal')");writer.commit()
    assert Path(str(source)+'-wal').exists()
    result=online.snapshot_sqlite(source,target,floor=0)
    assert result['integrity_verified'] is True
    with sqlite3.connect(target) as restored:
        assert restored.execute('SELECT count(*) FROM records').fetchone()[0]==2
    writer.execute("INSERT INTO records(value) VALUES ('after-point')");writer.commit()
    with sqlite3.connect(target) as restored:
        assert restored.execute('SELECT count(*) FROM records').fetchone()[0]==2
    assert writer.execute('SELECT count(*) FROM records').fetchone()[0]==3
    writer.close()


def test_online_snapshot_writer_can_commit_concurrently(tmp_path):
    source=tmp_path/'live.db';target=tmp_path/'snapshot.db';sqlite_db(source)
    started=threading.Event();stop=threading.Event();commits=[]
    def write():
        with sqlite3.connect(source,timeout=2) as db:
            db.execute('PRAGMA journal_mode=WAL');started.set()
            while not stop.wait(.005):
                db.execute("INSERT INTO records(value) VALUES ('concurrent')");db.commit();commits.append(True)
    thread=threading.Thread(target=write);thread.start();assert started.wait(2)
    try:
        online.snapshot_sqlite(source,target,floor=0)
        assert not stop.wait(.03)
    finally:stop.set();thread.join(2)
    assert commits
    online.verify_sqlite(target)


def test_foreign_key_failure_is_not_marked_verified(tmp_path):
    path=tmp_path/'invalid.db'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE parent(id INTEGER PRIMARY KEY)')
        db.execute('CREATE TABLE child(parent_id INTEGER REFERENCES parent(id))')
        db.execute('INSERT INTO child VALUES (9)')
    with pytest.raises(transport.BackupError,match='foreign-key'):
        online.verify_sqlite(path)


def test_reference_checks_require_actual_local_and_object_bytes(tmp_path):
    path=tmp_path/'point.db';sqlite_db(path,file_key='uploads/item')
    refs=online.database_references(path)
    with pytest.raises(transport.BackupError,match='reference'):
        online.verify_references(refs,{})
    digest=hashlib.sha256(b'document').hexdigest()
    online.verify_references(refs,{'data/files/uploads/item':{'sha256':digest,'bytes':8}})
    with pytest.raises(transport.BackupError,match='reference'):
        online.verify_references(refs,{'data/files/uploads/item':{'sha256':'f'*64,'bytes':8}})


def test_legacy_object_refs_exclude_incomplete_upload_metadata(tmp_path):
    path=tmp_path/'legacy.db'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE file_storage_uploads(object_ref TEXT,deletion_state TEXT)')
        db.executemany('INSERT INTO file_storage_uploads VALUES (?,?)',[('oss://materials/one','active'),('oss://materials/inflight','uploading')])
    assert online.database_references(path)==[{'key':'materials/one','backend':'oss-gateway','bytes':None,'sha256':None}]


@pytest.mark.parametrize('key',['../escape','/absolute','a/../b','a//b','a\\b','https://host/file','a/'])
def test_reference_member_traversal_is_rejected(key):
    with pytest.raises(transport.BackupError):online.relative_key(key)


def test_stable_copy_preserves_source_and_detects_rewrite(tmp_path,monkeypatch):
    source=tmp_path/'source';source.write_bytes(b'original')
    target=tmp_path/'private'/'copy'
    before=source.stat()
    result=online.copy_stable(source,target,floor=0)
    assert source.read_bytes()==target.read_bytes()==b'original'
    assert source.stat().st_mtime_ns==before.st_mtime_ns
    assert result['bytes']==8
    monkeypatch.setattr(online,'file_digest',lambda p: ('f'*64,8))
    with pytest.raises(transport.BackupError,match='content changed'):
        online.copy_stable(source,tmp_path/'different',floor=0)


def test_isolated_contents_checks_database_and_every_manifest_member(tmp_path):
    root=tmp_path/'contents';root.mkdir();db=root/'data'/'app.db';sqlite_db(db)
    sha,size=transport.sha_file(db)
    manifest={'files':{'data/app.db':{'sha256':sha,'bytes':size}},'databases':[{'member':'data/app.db'}],'references':[]}
    assert all(online.verify_contents(root,manifest).values())
    db.write_bytes(b'corrupted')
    with pytest.raises(transport.BackupError,match='hash mismatch'):
        online.verify_contents(root,manifest)


def test_online_proof_cannot_be_replaced_with_offline_true(tmp_path):
    metadata={'schemaVersion':3,'consistentOfflineSnapshot':True,'consistency':{}}
    with pytest.raises(transport.BackupError,match='consistency metadata'):
        transport.validate_online_consistency(metadata,tmp_path/'unused',None,'example')


@pytest.mark.parametrize('container_layer',[False,pytest.param(True,marks=pytest.mark.skipif(os.name=='nt',reason='Linux proc-root snapshot'))])
def test_online_point_upload_readback_and_isolated_db_file_git_restore(tmp_path,monkeypatch,container_layer):
    repo=tmp_path/'repository';repo.mkdir()
    online.run(['git','init',str(repo)])
    (repo/'source.py').write_text('print("never executed")\n')
    online.run(['git','-C',str(repo),'add','source.py'])
    online.run(['git','-C',str(repo),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','source'])
    commit=online.run(['git','-C',str(repo),'rev-parse','HEAD']).strip()
    data=tmp_path/'data';data.mkdir()
    db_path=tmp_path/'container-layer.db' if container_layer else data/'subsystem.db'
    sqlite_db(db_path,file_key='uploads/document')
    (data/'files/uploads').mkdir(parents=True);(data/'files/uploads/document').write_bytes(b'document')
    env=tmp_path/'app.env';env.write_text('EXAMPLE=fake-test-value\n');env.chmod(0o600)
    profile={'organizationId':'65130a23-b05e-4026-9615-761ab2d4193c','runtimeId':'example-runtime','enterpriseKey':'example','environment':'staging',
             'deployment':{'backupsRoot':str(tmp_path/'backups'),'deploymentsRoot':str(tmp_path/'deployments')},
             'backupStorage':{'provider':'aliyun-oss','namespaceMode':'enterprise-v1','bucket':'shared-backups','region':'cn-hangzhou','rootPrefix':'enterprises/65130a23-b05e-4026-9615-761ab2d4193c/staging/backups'}}
    release={'managedBy':online.MANAGED_BY,'applicationSlug':'example','containerName':'example','dataDir':str(data),'projectDir':str(repo),'envFile':str(env),'storageMode':'local-managed','current':{'commit':commit,'image':'example-image'}}
    path=tmp_path/'deployments/example/release.json';transport.atomic_json(path,release)
    identity={'id':'container','pid':os.getpid(),'running':True}
    monkeypatch.setattr(online,'container_identity',lambda r,p:identity)
    def bundle(project,required,destination):
        online.run(['git','-C',str(project),'bundle','create',str(destination),'--all'])
        destination.chmod(0o600);digest,_=transport.sha_file(destination)
        return {'bundleMember':'code/repository.bundle','bundleSha256':digest,'headCommit':commit,'requiredReleaseCommit':required,'restoreVerified':True,'uncommittedStateIncluded':False,'workingTreeClean':True}
    plan={'primary_sqlite':str(db_path) if container_layer else '/data/subsystem.db','capture_container_layout':False}
    point=online.capture_one(profile,'example',plan,runtime_helper=SimpleNamespace(backup_git_repository=bundle),floor=0)
    archive=Path(point['archive']);metadata=transport.read_json(archive.with_suffix('.gz.json'))
    assert metadata['schemaVersion']==3 and metadata['consistentOfflineSnapshot'] is False
    assert path.read_text()==json.dumps(release,sort_keys=True,ensure_ascii=False,separators=(',',':'))
    class Backend:
        def __init__(self):self.objects={};self.manifests={}
        def manifest(self,key):return self.manifests.get(key)
        def require_versioning(self):pass
        def head(self,key):return {'versionId':'pinned-version','size':len(self.objects[key])} if key in self.objects else None
        def upload(self,key,path,size,sha,journal):self.objects[key]=path.read_bytes();return self.head(key)
        def put_manifest(self,key,value):self.manifests[key]=value
        def get(self,key,version_id=None):assert version_id=='pinned-version';return io.BytesIO(self.objects[key])
        def assert_private(self,key,version):assert version=='pinned-version'
    backend=Backend();scope=transport.BackupScope(profile)
    published=transport.publish(scope,backend,'example',archive)
    assert published['snapshotSchemaVersion']==3 and published['offServer'] is True
    restored=transport.stage_restore(scope,backend,'example',archive.name,tmp_path/'isolated')
    assert restored['gitVerified'] and restored['businessDatabaseVerified'] and restored['fileHashesVerified'] and restored['referenceIntegrityVerified']
    assert restored['productionServicesStarted'] is False and restored['externalActionsExecuted'] is False
    assert (tmp_path/'isolated/contents/data/files/uploads/document').read_bytes()==b'document'
