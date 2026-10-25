#!/usr/bin/env python3
"""Private, enterprise-scoped off-server backup transport for trusted Runtime operators.

Consumes Runtime consistency archives. It never restores over running data, deletes
cloud objects, prints credentials, or treats an upload response as a verified backup.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.error import HTTPError
from uuid import UUID

CHUNK = 8 * 1024 * 1024
MAX_MANIFEST = 256 * 1024
SLUG = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
SHA = re.compile(r"^[a-f0-9]{64}$")
ARCHIVE = re.compile(r"^[0-9]{8}T[0-9]{6}(?:\.[0-9]{6})?Z-[a-f0-9]{12}\.tar\.gz$")
MANAGED_BY = "zhuojian-runtime-admin/v1"


class BackupError(RuntimeError):
    pass


def private_file(path: Path, *, allow_group_read=False):
    try:
        info = path.lstat()
    except OSError as exc:
        raise BackupError("required protected file is unavailable") from exc
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise BackupError("protected file must be regular and not a symlink")
    forbidden = 0o037 if allow_group_read else 0o077
    if os.name == "posix" and (info.st_uid != 0 or stat.S_IMODE(info.st_mode) & forbidden):
        raise BackupError("protected file must be root owned and mode 0600 or stricter")
    return info


def read_json(path: Path, maximum=MAX_MANIFEST, *, allow_group_read=False):
    info = private_file(path, allow_group_read=allow_group_read)
    if info.st_size > maximum:
        raise BackupError("metadata exceeds the supported size")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise BackupError("invalid protected JSON metadata") from exc
    if not isinstance(value, dict):
        raise BackupError("metadata must be an object")
    return value


def json_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix=".receipt-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(json_bytes(value)); handle.flush(); os.fsync(handle.fileno())
        os.chmod(name, 0o600)
        os.replace(name, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(name)


@contextlib.contextmanager
def publication_lock(path):
    """Serialize different Codex processes publishing the same recovery point."""
    fd=os.open(path,os.O_CREAT|os.O_RDWR|getattr(os,'O_NOFOLLOW',0),0o600)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or (os.name=='posix' and (info.st_uid!=0 or stat.S_IMODE(info.st_mode)&0o077)):
            raise BackupError('publication lock must be a private root-owned regular file')
        if os.name=='posix':
            import fcntl
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        else:
            import msvcrt
            if os.fstat(fd).st_size==0:os.write(fd,b'0')
            os.lseek(fd,0,os.SEEK_SET);msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
        yield
    except (BlockingIOError,PermissionError) as exc:
        raise BackupError('another publisher is handling this recovery point') from exc
    finally:
        os.close(fd)


def sha_file(path):
    h = hashlib.sha256(); size = 0
    with path.open("rb") as stream:
        while block := stream.read(CHUNK):
            h.update(block); size += len(block)
    return h.hexdigest(), size


def valid_slug(value):
    if not isinstance(value, str) or not SLUG.fullmatch(value):
        raise BackupError("invalid application slug")
    return value


class BackupScope:
    def __init__(self, profile):
        try:
            self.organization = str(UUID(str(profile["organizationId"])))
        except (ValueError, TypeError, KeyError) as exc:
            raise BackupError("Runtime organization identity is invalid") from exc
        self.environment = profile.get("environment")
        if self.environment not in {"development", "staging", "production"}:
            raise BackupError("Runtime environment is invalid")
        self.runtime = str(profile.get("runtimeId", ""))
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", self.runtime):
            raise BackupError("Runtime identifier is invalid")
        storage = profile.get("backupStorage") or {}
        if storage.get("provider") != "aliyun-oss" or storage.get("namespaceMode") != "enterprise-v1":
            raise BackupError("enterprise backup storage has not been initialized")
        self.prefix = f"enterprises/{self.organization}/{self.environment}/backups"
        if storage.get("rootPrefix") != self.prefix:
            raise BackupError("backup namespace does not match the Runtime enterprise")
        self.bucket = storage.get("bucket", "")
        self.region = storage.get("region", "")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,61}[a-z0-9]", self.bucket):
            raise BackupError("backup bucket is invalid")
        if not re.fullmatch(r"[a-z][a-z0-9-]{2,40}", self.region):
            raise BackupError("backup region is invalid")
        if self.bucket==(profile.get('objectStorage') or {}).get('bucket'):
            raise BackupError('private backups must use a separate bucket from business attachments')
        self.credential_file = Path(storage.get("credentialRef", "/etc/zhuojian/backup-oss.env"))
        deployment = profile.get("deployment") or {}
        self.backups = Path(deployment.get("backupsRoot", "/srv/zhuojian/backups"))
        self.deployments = Path(deployment.get("deploymentsRoot", "/srv/zhuojian/deployments"))

    def application_prefix(self, slug):
        return f"{self.prefix}/applications/{valid_slug(slug)}/"

    def archive_key(self, slug, archive_name):
        if not ARCHIVE.fullmatch(archive_name):
            raise BackupError("backup archive name is invalid")
        return self.application_prefix(slug) + "archives/" + archive_name

    def manifest_key(self, slug, archive_name):
        if not ARCHIVE.fullmatch(archive_name):
            raise BackupError("backup archive name is invalid")
        return self.application_prefix(slug) + "manifests/" + archive_name + ".json"


class OssBackend:
    """Official SDK only; root credentials are read from a protected file."""
    def __init__(self, scope):
        try:
            import oss2
        except ImportError as exc:
            raise BackupError("install the backup tool's oss2 dependency before use") from exc
        private_file(scope.credential_file)
        values = {}
        for line in scope.credential_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"): continue
            if "=" not in line: raise BackupError("invalid backup credential file")
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if key in values: raise BackupError("duplicate backup credential field")
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":value=value[1:-1]
            values[key] = value
        if values.get("OSS_BUCKET") != scope.bucket:
            raise BackupError("credential bucket and Runtime backup bucket differ")
        endpoint = values.get("OSS_ENDPOINT", "")
        parsed = urlsplit(endpoint)
        region = scope.region.removeprefix("oss-")
        hosts={f"oss-{region}.aliyuncs.com",f"oss-{region}-internal.aliyuncs.com"}
        if parsed.scheme != "https" or parsed.hostname not in hosts or parsed.port not in {None,443} or parsed.username or parsed.password or parsed.path not in {"","/"} or parsed.query or parsed.fragment:
            raise BackupError("backup endpoint does not match its region")
        if not values.get("OSS_ACCESS_KEY_ID") or not values.get("OSS_ACCESS_KEY_SECRET"):
            raise BackupError("backup credential fields are missing")
        token = values.get("OSS_SECURITY_TOKEN")
        auth=oss2.StsAuth(values['OSS_ACCESS_KEY_ID'],values['OSS_ACCESS_KEY_SECRET'],token) if token else oss2.Auth(values['OSS_ACCESS_KEY_ID'],values['OSS_ACCESS_KEY_SECRET'])
        self.sdk = oss2
        self.bucket = oss2.Bucket(auth, endpoint, scope.bucket, connect_timeout=30)
        self.endpoint_host=parsed.netloc
        self.bucket_name=scope.bucket

    @staticmethod
    def version(result):
        headers = {k.lower():v for k,v in (getattr(result,"headers",{}) or {}).items()}
        version = headers.get("x-oss-version-id")
        if not version or version == "null":
            raise BackupError("a non-null OSS object version is required for recoverable backup")
        return version

    def require_versioning(self):
        if self.bucket.get_bucket_versioning().status != "Enabled":
            raise BackupError("shared backup bucket versioning must be enabled once at initialization")

    def assert_private(self,key,version_id):
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):return None
        opener=build_opener(NoRedirect())
        base=f'https://{self.bucket_name}.{self.endpoint_host}/'+quote(key,safe='/')
        for suffix in ('','?'+urlencode({'versionId':version_id})):
            try:
                with opener.open(Request(base+suffix,headers={'Range':'bytes=0-0'}),timeout=30):
                    raise BackupError('backup object is anonymously readable')
            except HTTPError as exc:
                if exc.code==403:continue
                raise BackupError('backup anonymous-read denial could not be verified') from exc

    def assert_scope(self,scope):
        """Prove the configured RAM principal is confined to this enterprise backup prefix."""
        from uuid import uuid4
        nonce=uuid4().hex
        sibling=str(UUID(int=UUID(scope.organization).int ^ 1))
        prefixes=[f'backup-policy-probe/{nonce}/',f'enterprises/{sibling}/{scope.environment}/backups/{nonce}/',f'enterprises/{scope.organization}/{scope.environment}/apps/{nonce}/']
        for prefix in prefixes:
            key=prefix+'missing.bin'
            actions=[lambda:self.bucket.list_objects_v2(prefix=prefix,max_keys=1),lambda:self.bucket.head_object(key),lambda:self.bucket.delete_object(key),lambda:self.bucket.put_object(key,b'invalid-md5-probe',headers={'Content-MD5':'AAAAAAAAAAAAAAAAAAAAAA=='})]
            for action in actions:
                try:action()
                except Exception as exc:
                    if getattr(exc,'status',None)==403:continue
                    raise BackupError('could not verify enterprise backup credential boundary') from exc
                raise BackupError('backup credential permits access outside this enterprise backup namespace')

    def head(self,key):
        try:
            result=self.bucket.head_object(key)
        except Exception as exc:
            if getattr(exc,"status",None)==404:return None
            raise BackupError("backup object readback is unavailable; keep local data") from exc
        return {"versionId":self.version(result),"size":int(result.content_length)}

    def get(self,key,version_id=None):
        return self.bucket.get_object(key,params={"versionId":version_id} if version_id else None)

    def manifest(self,key):
        head=self.head(key)
        if head is None:return None
        if head['size']>MAX_MANIFEST:raise BackupError("remote manifest is too large")
        body=self.get(key,head['versionId'])
        try:raw=body.read(MAX_MANIFEST+1)
        finally:body.close()
        if len(raw)>MAX_MANIFEST:raise BackupError("remote manifest is too large")
        try:value=json.loads(raw)
        except ValueError as exc:raise BackupError("remote manifest is invalid") from exc
        return value

    def put_manifest(self,key,value):
        data=json_bytes(value)
        result=self.bucket.put_object(key,data,headers={"Content-Type":"application/json","x-oss-server-side-encryption":"AES256","x-oss-object-acl":"private","x-oss-forbid-overwrite":"true"})
        return self.version(result)

    def upload(self,key,path,size,sha,journal):
        state=read_json(journal) if journal.exists() else {}
        identity={"objectKey":key,"sha256":sha,"sizeBytes":size}
        if state and any(state.get(k)!=v for k,v in identity.items()):raise BackupError("upload journal belongs to another backup")
        upload_id=state.get("uploadId")
        if state.get('phase')=='initiating':
            # OSS ListMultipartUploads is bucket-wide and does not support the
            # oss:Prefix RAM condition. Do not grant tenant root that permission.
            raise BackupError('upload initialization outcome is unknown; preserve this recovery point and journal, create a new Runtime backup, and publish its distinct archive ID')
        elif state.get('phase')=='completing':
            if not upload_id:raise BackupError('completion journal has no upload identity')
            # A completed upload is handled by HEAD/full GET before this call.
            # Only resume the same still-active multipart operation.
            try:self.bucket.list_parts(key,upload_id,max_parts=1)
            except Exception as exc:raise BackupError('completion outcome still unknown; preserve the journal and retry object readback') from exc
            atomic_json(journal,{**identity,'phase':'uploading','uploadId':upload_id})
        elif state.get('phase')=='uploaded':
            raise BackupError('previously uploaded object is no longer discoverable; do not create a replacement version')
        if not upload_id:
            atomic_json(journal,{**identity,"phase":"initiating"})
            result=self.bucket.init_multipart_upload(key,headers={"Content-Type":"application/gzip","x-oss-meta-sha256":sha,"x-oss-server-side-encryption":"AES256","x-oss-object-acl":"private","x-oss-forbid-overwrite":"true"})
            upload_id=result.upload_id
            atomic_json(journal,{**identity,"phase":"uploading","uploadId":upload_id})
        parts=[]
        # Re-uploading the same numbered part is idempotent. No >512 MiB buffer.
        part_size=max(CHUNK, (size+9999)//10000)
        with path.open('rb') as handle:
            number=1
            while block:=handle.read(part_size):
                result=self.bucket.upload_part(key,upload_id,number,block)
                parts.append(self.sdk.models.PartInfo(number,result.etag));number+=1
        atomic_json(journal,{**identity,"phase":"completing","uploadId":upload_id})
        result=self.bucket.complete_multipart_upload(key,upload_id,parts)
        version=self.version(result)
        atomic_json(journal,{**identity,"phase":"uploaded","uploadId":upload_id,"versionId":version})
        return {"versionId":version,"size":size}

    def list_manifest_keys(self,prefix):
        for item in self.sdk.ObjectIteratorV2(self.bucket,prefix=prefix):
            if item.key.endswith('.tar.gz.json'):yield item.key


def validate_manifest(scope,slug,archive_name,manifest):
    if not isinstance(manifest,dict):raise BackupError("remote manifest must be an object")
    expected={"schemaVersion":1,"organizationId":scope.organization,"environment":scope.environment,"applicationSlug":valid_slug(slug),"bucket":scope.bucket,"archive":archive_name,"objectKey":scope.archive_key(slug,archive_name),"status":"verified"}
    if type(manifest.get('schemaVersion')) is not int or any(manifest.get(k)!=v for k,v in expected.items()):raise BackupError("remote manifest is outside the requested enterprise or backup")
    if not SHA.fullmatch(str(manifest.get('sha256',''))) or type(manifest.get('sizeBytes')) is not int or manifest['sizeBytes']<=0:
        raise BackupError("remote backup integrity fields are invalid")
    if not isinstance(manifest.get('versionId'),str) or not manifest['versionId'] or manifest['versionId']=='null':raise BackupError("remote backup version is missing")
    validate_source(manifest.get('source'))
    if manifest.get('commit') != manifest['source']['requiredReleaseCommit']:
        raise BackupError('remote backup source does not match its recorded running commit')
    return manifest


def validate_source(source):
    if not isinstance(source,dict) or source.get('restoreVerified') is not True or source.get('bundleMember')!='code/repository.bundle' or not SHA.fullmatch(str(source.get('bundleSha256',''))):
        raise BackupError('backup Git recovery proof is missing or invalid')
    if any(not re.fullmatch(r'[a-f0-9]{40}',str(source.get(field,''))) for field in ('headCommit','requiredReleaseCommit')):
        raise BackupError('backup Git recovery commit is invalid')
    if source.get('uncommittedStateIncluded') is not False:
        raise BackupError('backup must explicitly describe its committed Git recovery scope')
    if 'workingTreeClean' in source and type(source['workingTreeClean']) is not bool:
        raise BackupError('backup working tree state must be an explicit boolean')


def verify_remote(backend,manifest,destination=None):
    body=backend.get(manifest['objectKey'],manifest['versionId'])
    h=hashlib.sha256();size=0
    try:
        while block:=body.read(CHUNK):
            size+=len(block)
            if size>manifest['sizeBytes']:raise BackupError("remote object size exceeds the manifest")
            h.update(block)
            if destination is not None:destination.write(block)
    finally:body.close()
    if size!=manifest['sizeBytes'] or h.hexdigest()!=manifest['sha256']:
        raise BackupError("remote object SHA-256 or size mismatch; keep local recovery points")
    return size


def publish(scope,backend,slug,archive_path):
    path=Path(archive_path)
    private_file(path)
    with publication_lock(path.with_suffix(path.suffix+'.publish.lock')):
        return _publish(scope,backend,slug,path)


def _publish(scope,backend,slug,archive_path):
    valid_slug(slug);archive_path=Path(archive_path)
    private_file(archive_path)
    expected_dir=(scope.backups/slug).resolve()
    if archive_path.parent.resolve()!=expected_dir:raise BackupError("archive must be in this application's managed backup directory")
    key=scope.archive_key(slug,archive_path.name)
    metadata=read_json(archive_path.with_suffix(archive_path.suffix+'.json'))
    source=metadata.get('source') or {}
    if type(metadata.get('schemaVersion')) is not int or metadata['schemaVersion'] != 2 or metadata.get('managedBy')!=MANAGED_BY or metadata.get('applicationSlug')!=slug or metadata.get('archive')!=archive_path.name or metadata.get('consistentOfflineSnapshot') is not True or source.get('restoreVerified') is not True:
        raise BackupError("backup must include a Runtime-verified consistency snapshot and Git recovery bundle")
    validate_source(source)
    if metadata.get('commit') != source['requiredReleaseCommit']:
        raise BackupError('backup source does not match its recorded running commit')
    source={key:source[key] for key in ('bundleMember','bundleSha256','headCommit','requiredReleaseCommit','uncommittedStateIncluded','restoreVerified','workingTreeClean') if key in source}
    sha,size=sha_file(archive_path)
    if metadata.get('sha256')!=sha or metadata.get('sizeBytes')!=size:raise BackupError("local archive does not match its verified metadata")
    manifest_key=scope.manifest_key(slug,archive_path.name)
    existing=backend.manifest(manifest_key)
    receipt_path=archive_path.with_suffix(archive_path.suffix+'.remote.json')
    if existing is not None:
        validate_manifest(scope,slug,archive_path.name,existing)
        if existing['sha256']!=sha or existing['sizeBytes']!=size:raise BackupError("existing backup ID has different content")
        verify_remote(backend,existing)
        backend.assert_private(key,existing['versionId'])
        atomic_json(receipt_path,existing)
        return {**existing,'reused':True}
    backend.require_versioning()
    head=backend.head(key)
    if head is None:
        journal=archive_path.with_suffix(archive_path.suffix+'.upload.json')
        head=backend.upload(key,archive_path,size,sha,journal)
    manifest={"schemaVersion":1,"organizationId":scope.organization,"environment":scope.environment,"runtimeId":scope.runtime,"applicationSlug":slug,"bucket":scope.bucket,"archive":archive_path.name,"objectKey":key,"versionId":head['versionId'],"sha256":sha,"sizeBytes":size,"commit":metadata.get('commit'),"source":source,"status":"verified","offServer":True,"createdAt":metadata.get('createdAt')}
    verify_remote(backend,manifest)
    backend.assert_private(key,manifest['versionId'])
    try:
        backend.put_manifest(manifest_key,manifest)
    except Exception as exc:
        # Unknown manifest write is only read back; a different value is never overwritten.
        recovered=backend.manifest(manifest_key)
        if recovered!=manifest:raise BackupError("manifest outcome is unknown; keep the local backup and inspect this same backup ID") from exc
    stored=backend.manifest(manifest_key)
    if stored!=manifest:raise BackupError("remote manifest readback differs from the verified backup")
    atomic_json(receipt_path,manifest)
    return {**manifest,'reused':False}


def discover(scope,backend,slug):
    prefix=scope.application_prefix(slug)+'manifests/'
    results=[]
    for key in backend.list_manifest_keys(prefix):
        if not key.startswith(prefix):raise BackupError("storage listing escaped the enterprise prefix")
        name=key[len(prefix):]
        if '/' in name or not name.endswith('.json'):continue
        archive_name=name[:-5]
        if not ARCHIVE.fullmatch(archive_name):continue
        manifest=validate_manifest(scope,slug,archive_name,backend.manifest(key))
        results.append(manifest)
    return sorted(results,key=lambda x:x['archive'],reverse=True)


def download(scope,backend,slug,archive_name,destination):
    manifest=validate_manifest(scope,slug,archive_name,backend.manifest(scope.manifest_key(slug,archive_name)))
    backend.assert_private(manifest['objectKey'],manifest['versionId'])
    destination=Path(destination)
    if destination.exists() or destination.is_symlink():raise BackupError("recovery directory must not already exist")
    if not destination.parent.is_dir() or shutil.disk_usage(destination.parent).free < manifest['sizeBytes'] + 64 * 1024 * 1024:
        raise BackupError('not enough disk space to download this isolated recovery point')
    # New isolated directory only. No automatic extraction, Git checkout or live restore.
    destination.mkdir(parents=False,mode=0o700)
    partial=destination/(archive_name+'.partial')
    try:
        with partial.open('xb') as handle:
            os.chmod(partial,0o600);verify_remote(backend,manifest,handle)
            handle.flush();os.fsync(handle.fileno())
        final=destination/archive_name
        os.replace(partial,final)
        atomic_json(destination/(archive_name+'.remote.json'),manifest)
        return {'ok':True,'status':'downloaded_and_verified','directory':str(destination),'archive':str(final),'sha256':manifest['sha256'],'restoredToLive':False}
    except BaseException:
        # Keep the uniquely named directory/partial as evidence. Never touch live state.
        raise


def stage_restore(scope,backend,slug,archive_name,destination):
    result=download(scope,backend,slug,archive_name,destination)
    destination=Path(destination)
    target=destination/'contents';target.mkdir(mode=0o700)
    with tarfile.open(result['archive'],'r:gz') as archive:
        members=archive.getmembers()
        if len(members)>100000:raise BackupError('backup has too many restore members')
        total=0
        for member in members:
            parts=PurePosixPath(member.name).parts
            if not parts or parts[0] not in {'data','config','code'} or any(p in {'..','.'} for p in parts) or '\\' in member.name or ':' in member.name or PurePosixPath(member.name).is_absolute() or not (member.isfile() or member.isdir()):
                raise BackupError('backup contains an unsafe restore member')
            total+=member.size
        bundle_size=sum(member.size for member in members if member.name=='code/repository.bundle')
        if shutil.disk_usage(destination).free < total+2*bundle_size+64*1024*1024:
            raise BackupError('not enough disk space for this isolated restore')
        for member in members:
            output=target/member.name
            if member.isdir():output.mkdir(parents=True,exist_ok=True,mode=0o700);continue
            output.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            with archive.extractfile(member) as source,output.open('xb') as handle:
                os.chmod(output,0o600);shutil.copyfileobj(source,handle,CHUNK)
    manifest=read_json(destination/(archive_name+'.remote.json'))
    source=manifest.get('source') or {}
    validate_source(source)
    bundle=target/'code'/'repository.bundle'
    actual,_=sha_file(bundle)
    if actual!=source.get('bundleSha256'):raise BackupError('Git recovery bundle hash mismatch')
    repo=destination/'git-restore-check'
    git_environment={key:value for key,value in os.environ.items() if not key.upper().startswith('GIT_')}
    git_environment.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_TERMINAL_PROMPT='0')
    for command in [['git','init','--bare',str(repo)],['git','-C',str(repo),'bundle','verify',str(bundle)],['git','clone','--bare',str(bundle),str(destination/'repository.git')]]:
        p=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=120,env=git_environment)
        if p.returncode:raise BackupError('isolated Git bundle recovery failed')
    for commit in {source.get('headCommit'),source.get('requiredReleaseCommit')}:
        if not isinstance(commit,str) or not re.fullmatch(r'[a-f0-9]{40}',commit):raise BackupError('backup Git commit metadata is invalid')
        p=subprocess.run(['git','-C',str(destination/'repository.git'),'cat-file','-e',commit+'^{commit}'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,env=git_environment)
        if p.returncode:raise BackupError('required Git recovery commit is missing')
    result.update(status='isolated_restore_verified',gitVerified=True,extractedDirectory=str(target),businessDatabaseVerified=False)
    atomic_json(destination/'restore-check.json',result)
    return result


def prune_local(scope,backend,slug,keep,apply=False):
    valid_slug(slug)
    if keep<2:raise BackupError('keep at least two newest local recovery points')
    archives=sorted((scope.backups/slug).glob('*.tar.gz'),reverse=True)
    result={'ok':True,'applicationSlug':slug,'keptNewest':keep,'apply':apply,'removed':[],'candidates':[],'preserved':[]}
    for path in archives[keep:]:
        try:
            private_file(path)
            with publication_lock(path.with_suffix('.gz.publish.lock')):
                manifest=validate_manifest(scope,slug,path.name,backend.manifest(scope.manifest_key(slug,path.name)))
                validate_source(manifest.get('source'))
                sha,size=sha_file(path)
                if (sha,size)!=(manifest['sha256'],manifest['sizeBytes']):raise BackupError('local backup differs from remote receipt')
                result['candidates'].append(path.name)
                if not apply:continue
                # Re-download exactly the recorded remote version before local
                # removal; a historic upload receipt alone is insufficient.
                verify_remote(backend,manifest)
                backend.assert_private(manifest['objectKey'],manifest['versionId'])
                owned=[path]+[p for p in [path.with_suffix('.gz.json'),path.with_suffix('.gz.upload.json')] if p.exists()]
                for candidate in owned:private_file(candidate)
                atomic_json(path.with_suffix('.gz.remote.json'),manifest)
                for candidate in owned:candidate.unlink()
                result['removed'].append(path.name)
        except Exception:
            result['preserved'].append({'archive':path.name,'reason':'remote proof unavailable or local state unsafe'})
    return result


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime-profile',type=Path,default=Path('/etc/zhuojian/runtime.json'))
    sub=p.add_subparsers(dest='command',required=True)
    configure=sub.add_parser('configure')
    configure.add_argument('--bucket',required=True);configure.add_argument('--region',required=True)
    configure.add_argument('--credential-file',type=Path,default=Path('/etc/zhuojian/backup-oss.env'))
    pub=sub.add_parser('publish');pub.add_argument('application_slug');pub.add_argument('--archive',type=Path,required=True)
    sub.add_parser('publish-latest')
    ls=sub.add_parser('list');ls.add_argument('application_slug')
    verify=sub.add_parser('verify');verify.add_argument('application_slug');verify.add_argument('--archive-name',required=True)
    get=sub.add_parser('download');get.add_argument('application_slug');get.add_argument('--archive-name',required=True);get.add_argument('--destination',type=Path,required=True)
    stage=sub.add_parser('stage-restore');stage.add_argument('application_slug');stage.add_argument('--archive-name',required=True);stage.add_argument('--destination',type=Path,required=True)
    prune=sub.add_parser('prune-local');prune.add_argument('application_slug');prune.add_argument('--keep',type=int,default=7);prune.add_argument('--apply',action='store_true')
    sub.add_parser('probe')
    sub.add_parser('status')
    return p


def main(argv=None):
    args=parser().parse_args(argv)
    try:
        if os.name=='posix' and os.geteuid()!=0:raise BackupError("backup operations require the authorized Runtime root environment")
        if args.command=='configure':
            # Same host-wide lock as the Runtime publisher prevents lost profile
            # updates; this configures storage only, never cloud IAM or buckets.
            with publication_lock(Path('/run/lock/zhuojian-runtime-admin.lock')):
                profile=read_json(args.runtime_profile,allow_group_read=True)
                try:organization=str(UUID(str(profile['organizationId'])))
                except (ValueError,KeyError) as exc:raise BackupError('Runtime enterprise identity is invalid') from exc
                storage={'provider':'aliyun-oss','namespaceMode':'enterprise-v1','bucket':args.bucket,'region':args.region,
                         'rootPrefix':f"enterprises/{organization}/{profile.get('environment')}/backups",'credentialRef':str(args.credential_file)}
                current=profile.get('backupStorage')
                if current and any(current.get(k)!=v for k,v in storage.items()):
                    raise BackupError('existing backup storage differs; preserve its recovery points and use an explicit migration plan')
                candidate={**profile,'backupStorage':storage}
                scope=BackupScope(candidate);backend=OssBackend(scope)
                backend.assert_scope(scope);backend.require_versioning()
                storage['boundaryVerified']=True
                atomic_json(args.runtime_profile,candidate)
                print(json.dumps({'ok':True,'configured':True,'rootPrefix':scope.prefix,'uploadVerified':False}));return 0
        scope=BackupScope(read_json(args.runtime_profile,allow_group_read=True))
        if args.command=='status':
            print(json.dumps({'ok':True,'configured':True,'organizationId':scope.organization,'environment':scope.environment,'bucket':scope.bucket,'rootPrefix':scope.prefix,'cloudVerified':False}));return 0
        backend=OssBackend(scope)
        backend.assert_scope(scope)
        if args.command=='probe':
            backend.require_versioning();print(json.dumps({'ok':True,'enterpriseBoundaryVerified':True,'versioningEnabled':True,'uploadVerified':False}));return 0
        if args.command=='publish':result=publish(scope,backend,args.application_slug,args.archive)
        elif args.command=='publish-latest':
            result={'ok':True,'backups':[],'failed':[]}
            for release_path in sorted(scope.deployments.glob('*/release.json')):
                slug=valid_slug(release_path.parent.name)
                try:
                    release=read_json(release_path,allow_group_read=True)
                    if release.get('managedBy')!=MANAGED_BY:continue
                    if release.get('applicationSlug') != slug:
                        raise BackupError('managed release identity differs from its application directory')
                    archives=sorted((scope.backups/slug).glob('*.tar.gz'),reverse=True)
                    if not archives:raise BackupError("no local consistency backup exists")
                    result['backups'].append(publish(scope,backend,slug,archives[0]))
                except Exception:
                    result['failed'].append({'applicationSlug':slug,'status':'not_uploaded_or_not_verified','localPreserved':True})
            if result['failed']:result['ok']=False
        elif args.command=='list':result={'ok':True,'backups':discover(scope,backend,args.application_slug)}
        elif args.command=='verify':
            manifest=validate_manifest(scope,args.application_slug,args.archive_name,backend.manifest(scope.manifest_key(args.application_slug,args.archive_name)))
            verify_remote(backend,manifest);backend.assert_private(manifest['objectKey'],manifest['versionId']);result={'ok':True,'status':'verified','backup':manifest}
        elif args.command=='stage-restore':result=stage_restore(scope,backend,args.application_slug,args.archive_name,args.destination)
        elif args.command=='prune-local':result=prune_local(scope,backend,args.application_slug,args.keep,args.apply)
        else:result=download(scope,backend,args.application_slug,args.archive_name,args.destination)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 0 if result.get('ok',True) else 2
    except BackupError as exc:
        print(json.dumps({'ok':False,'error':str(exc),'localPreserved':True}),file=sys.stderr);return 2
    except Exception:
        print(json.dumps({'ok':False,'error':'backup transport failed; inspect saved state without resubmitting unknown writes','localPreserved':True}),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
