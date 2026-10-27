#!/usr/bin/env python3
"""Observe existing private receipts only; publish a safe v1 recovery projection.

No cloud SDK/client, archive/object body, backup/restore invocation, Docker access,
or business database access is used. Observation time is refreshed; point times
are preserved from original receipts.
"""
from __future__ import annotations
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys

import runtime_backup_oss as transport

OUTPUT=Path('/var/lib/zhuojian-operations/recovery-points-source.json')
IDENTIFIER=re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}$')


def unknown_component():
    return {'included':None,'verified':None,'count':None,'bytes':None}


def project_point(profile,slug,app,metadata,path):
    if metadata.get('applicationSlug')!=slug or metadata.get('archive')!=path.name or not transport.SHA.fullmatch(str(metadata.get('sha256',''))):
        raise transport.BackupError('backup receipt identity is invalid')
    version=metadata.get('schemaVersion')
    if version not in {2,3}:raise transport.BackupError('unsupported local recovery receipt')
    components=metadata.get('components') if version==3 else None
    if components is None:
        components={k:unknown_component() for k in ['database','local_files','oss_files','code','config']}
        components['oss_files']={'included':False,'verified':None,'count':0,'bytes':0}
        if app.get('primary_sqlite','').startswith('/app/'):
            components['database']={'included':False,'verified':None,'count':0,'bytes':0}
    offsite={'status':'pending' if profile.get('backupStorage') else 'not_configured','uploaded_at':None,'full_readback_at':None,'sha256':None,'version_pinned':None}
    remote_path=path.with_suffix(path.suffix+'.remote.json')
    if remote_path.is_file():
        remote=transport.read_json(remote_path)
        if remote.get('archive')==path.name and remote.get('sha256')==metadata['sha256'] and remote.get('applicationSlug')==slug and remote.get('offServer') is True:
            uploaded=remote.get('uploadedAt');readback=remote.get('fullReadbackAt')
            offsite={'status':'verified' if uploaded and readback else 'unknown','uploaded_at':uploaded,'full_readback_at':readback,
                     'sha256':remote['sha256'],'version_pinned':bool(remote.get('versionId') and remote.get('versionId')!='null')}
    restore={'result':'not_tested','verified_at':None,'database_integrity':None,'git_commit':None,'file_hashes':None,'reference_integrity':None,'limitations':[]}
    restored_path=path.with_suffix(path.suffix+'.restore.json')
    if restored_path.is_file():
        receipt=transport.read_json(restored_path)
        if receipt.get('archiveName')==path.name and receipt.get('sha256')==metadata['sha256'] and receipt.get('verifiedAt'):
            checks={'database_integrity':receipt.get('businessDatabaseVerified'),'git_commit':receipt.get('gitVerified'),
                    'file_hashes':receipt.get('fileHashesVerified'),'reference_integrity':receipt.get('referenceIntegrityVerified')}
            if all(v is True for v in checks.values()):
                restore={'result':'partial','verified_at':receipt['verifiedAt'],**checks,'limitations':['restore_scope_limited','runtime_services_not_started','config_restore_not_tested']}
    limits=list(metadata.get('limitations') or [])
    if version==2:limits+=['legacy_data_scope_unverified','oss_body_excluded']
    if offsite['status']!='verified':limits.append('offsite_not_verified')
    return {'point_id':path.name,'captured_at':metadata.get('capturedAt',metadata['createdAt']),'completed_at':metadata['createdAt'],
            'source_commit':metadata.get('commit'),'project_ids':[],'shared_archive_group':None,'archive_bytes':metadata.get('sizeBytes'),
            'components':components,'local_archive_exists':path.is_file() and not path.is_symlink(),
            'offsite':offsite,'restore':restore,'limitations':sorted(set(limits))}


def observe(profile,plan,now=None):
    for key in ['organizationId','runtimeId','environment']:
        if profile.get(key)!=plan.get(key):raise transport.BackupError('recovery projection plan identity differs')
    source=plan.get('source_id');host=plan.get('host_id')
    if not isinstance(source,str) or not IDENTIFIER.fullmatch(source) or not isinstance(host,str) or not IDENTIFIER.fullmatch(host):
        raise transport.BackupError('registered recovery source identity is missing')
    now=now or dt.datetime.now(dt.timezone.utc).isoformat()
    backups=Path(profile.get('deployment',{}).get('backupsRoot','/srv/zhuojian/backups'))
    systems=[]
    for slug,app in sorted(plan['applications'].items()):
        transport.valid_slug(slug);root=backups/slug
        if root.is_symlink():raise transport.BackupError('recovery receipt directory cannot be a symlink')
        latest=None
        for metadata_path in sorted(root.glob('*.tar.gz.json'),reverse=True):
            metadata=transport.read_json(metadata_path)
            if not transport.ARCHIVE.fullmatch(metadata_path.name.removesuffix('.json')):continue
            if metadata.get('schemaVersion') not in {2,3}:continue
            latest=project_point(profile,slug,app,metadata,metadata_path.with_suffix(''));break
        job={'status':'not_run','attempt_at':None,'finished_at':None,'next_run_at':None,'error_code':None}
        job_path=root/'online-job.json'
        if job_path.is_file():
            private=transport.read_json(job_path)
            job={k:private.get(k) for k in ['status','attempt_at','finished_at','error_code']}
            job['next_run_at']=None
            if latest and private.get('archive')==latest['point_id'] and private.get('status')=='failed' and private.get('error_code')=='offsite_failed':
                latest['offsite']['status']='failed'
        systems.append({'system_id':source+':'+slug,'source_id':source,'host_id':host,'name':app['name'],'scope':'enterprise',
                        'organization_id':profile['organizationId'],'enterprise_key':profile['enterpriseKey'],'runtime_id':profile['runtimeId'],
                        'project_id':None,'application_slug':slug,'environment':profile['environment'],'observed_at':now,
                        'latest_job':job,'latest_successful_point':latest})
    return {'schema_version':1,'observed_at':now,'systems':systems}


def main():
    try:
        if os.name!='posix' or os.geteuid()!=0:raise transport.BackupError('recovery observation requires Runtime root')
        profile=transport.read_json(Path('/etc/zhuojian/runtime.json'),allow_metadata_read=True)
        plan=transport.read_json(Path('/etc/zhuojian/backup-online-plan.json'))
        value=observe(profile,plan)
        if OUTPUT.parent.exists():
            info=OUTPUT.parent.lstat()
            if OUTPUT.parent.is_symlink() or info.st_uid!=0 or info.st_mode&0o022:
                raise transport.BackupError('unsafe recovery projection directory')
        transport.atomic_json(OUTPUT,value)
        print(json.dumps({'ok':True,'observed_at':value['observed_at'],'system_count':len(value['systems'])}))
        return 0
    except Exception:
        print(json.dumps({'ok':False,'error_code':'source_unavailable'}),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
