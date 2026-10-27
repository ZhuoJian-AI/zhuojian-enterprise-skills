#!/usr/bin/env python3
"""Install Alphabet's online-only cloud backup schedule after real point gates.

Dry run by default. Keeps old units and wrappers for reviewed rollback; never
starts/stops business services, accepts Windows ACKs, or deletes archives.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile

MACHINE='24b1027fbbb34fe080910773ec63ebc9'
ORG='65130a23-b05e-4026-9615-761ab2d4193c'
ROOT=Path('/etc/zhuojian/integrations/alphabet-online-backup-20261028')
OLD='zhuojian-backup.timer'
NEW='zhuojian-online-backup.timer'
FLOOR=5*1024**3

PREFLIGHT='''import hashlib,json,os,shutil,stat,sys
from pathlib import Path
ROOT=Path(__file__).parent
def private(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and not p.is_symlink() and s.st_mode&0o077==0
 return p.read_bytes()
assert os.geteuid()==0 and Path('/etc/machine-id').read_text().strip()==MACHINE
pins=json.loads(private(ROOT/'pins.json'))
for name,expected in pins['wrappers'].items():
 p=Path('/usr/local/sbin')/name;s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and not p.is_symlink() and s.st_mode&0o022==0
 assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
plan_raw=private(Path('/etc/zhuojian/backup-online-plan.json'));assert hashlib.sha256(plan_raw).hexdigest()==pins['plan_sha256']
plan=json.loads(plan_raw);profile=json.loads(Path('/etc/zhuojian/runtime.json').read_bytes())
assert plan['organizationId']==profile['organizationId']==ORG and plan['runtimeId']==profile['runtimeId']=='aifabei-hk-01' and plan['environment']==profile['environment']=='staging'
assert len(plan['applications'])==9
assert shutil.disk_usage('/srv/zhuojian').free>=5*1024**3
if len(sys.argv)>1 and sys.argv[1]=='windows':
 # Preserve the existing exporter's own capacity estimate, plus headroom for
 # the next primary capture. A laptop/cache failure cannot block cloud points.
 import importlib.util
 p=Path('/etc/zhuojian/integrations/alphabet-offsite-backup-20261025/backup_policy.py')
 spec=importlib.util.spec_from_file_location('existing_windows_policy',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 config=m.load_config();_,budget,_=m.capacity_estimates(config)
 peak=0
 for slug in plan['applications']:
  rows=sorted((Path('/srv/zhuojian/backups')/slug).glob('*.tar.gz.json'),reverse=True)
  if rows:
   v=json.loads(private(rows[0]));c=v.get('components',{})
   estimated=sum((c.get(k) or {}).get('bytes') or 0 for k in ['database','local_files','oss_files'])
   peak=max(peak,estimated*3+64*1024**2,v.get('restoreRequiredFreeBytes',0))
 assert shutil.disk_usage('/srv/zhuojian').free>=max(config['recovery_free_floor_bytes'],5*1024**3)+budget+peak
'''.replace('MACHINE',repr(MACHINE)).replace('ORG',repr(ORG))


def units():
    preflight=str(ROOT/'preflight.py')
    return {
      'zhuojian-online-backup.service':f'''[Unit]
Description=Alphabet online database, files and exact-version cloud recovery points
After=network-online.target docker.service
Wants=network-online.target
RequiresMountsFor=/srv/zhuojian
OnSuccess=zhuojian-backup-windows-export.service

[Service]
Type=oneshot
User=root
UMask=0077
Nice=10
IOSchedulingClass=idle
CPUWeight=20
IOWeight=10
MemoryAccounting=true
CPUAccounting=true
TimeoutStartSec=10800
ExecStartPre=/usr/bin/python3 {preflight}
ExecStart=/usr/local/sbin/zhuojian-online-backup --publish --verify-restore all
''',
      'zhuojian-online-backup.timer':'''[Unit]
Description=Daily Alphabet online cloud recovery points

[Timer]
OnCalendar=*-*-* 03:15:00
RandomizedDelaySec=15m
AccuracySec=1m
Persistent=true
Unit=zhuojian-online-backup.service

[Install]
WantedBy=timers.target
''',
      'zhuojian-backup-windows-export.service':f'''[Unit]
Description=Secondary Alphabet Windows export cache, independent of cloud backups
RequiresMountsFor=/srv/zhuojian

[Service]
Type=oneshot
User=root
UMask=0077
Nice=15
IOSchedulingClass=idle
TimeoutStartSec=1800
ExecStartPre=/usr/bin/python3 {preflight} windows
ExecStart=/usr/bin/python3 /etc/zhuojian/integrations/alphabet-offsite-backup-20261025/export_latest.py
'''}


def command(*args,check=True):
    r=subprocess.run(list(args),capture_output=True,text=True,timeout=60)
    if check and r.returncode:raise RuntimeError('schedule control command failed')
    return r


def regular(path,private=False):
    s=path.lstat()
    assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and not path.is_symlink()
    if os.name=='posix':assert s.st_mode&(0o077 if private else 0o022)==0
    return path.read_bytes()


def atomic(path,raw,mode):
    fd,name=tempfile.mkstemp(prefix='.online-schedule-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        os.chmod(name,mode);os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)


def point_gate(root,scope,slug,t):
    valid=[];pruned=[];unverified=0
    for meta_path in sorted(root.glob('*.tar.gz.json'),reverse=True):
        try:
            meta=json.loads(regular(meta_path,True))
            if meta.get('schemaVersion')!=3:continue
            archive=meta_path.with_suffix('')
            proof=json.loads(regular(archive.with_suffix('.gz.restore.json'),True))
            remote=t.validate_manifest(scope,slug,archive.name,json.loads(regular(archive.with_suffix('.gz.remote.json'),True)))
            assert meta['archive']==archive.name and meta['applicationSlug']==slug
            assert proof['archiveName']==archive.name and proof['sha256']==meta['sha256']==remote['sha256'] and proof['versionId']==remote['versionId']
            assert all(proof.get(k) is True for k in ['businessDatabaseVerified','gitVerified','fileHashesVerified','referencesRequeried'])
            assert proof.get('referenceIntegrityVerified') is True or (slug=='garment-production-collaboration' and proof.get('sourceMissingBaselineVerified') is True and 0<proof.get('sourceMissingReferenceCount',0)<=275)
            assert remote.get('fullReadbackAt') and remote.get('offServer') is True and remote['versionId']!='null'
            if archive.exists() or archive.is_symlink():
                before=t.private_file(archive);sha,size=t.sha_file(archive);after=t.private_file(archive)
                signature=lambda v:(v.st_dev,v.st_ino,v.st_size,v.st_mtime_ns,v.st_ctime_ns)
                assert signature(before)==signature(after) and (sha,size)==(meta['sha256'],meta['sizeBytes'])==(remote['sha256'],remote['sizeBytes'])
                valid.append(archive.name)
            else:
                p=json.loads(regular(archive.with_suffix('.gz.pruned.json'),True))
                assert p['archive']==archive.name and p['sha256']==remote['sha256'] and p['versionId']==remote['versionId'] and p['bytes']==remote['sizeBytes']
                assert p['isolatedRestoreMatched'] is True and p['exactRemoteVersionReadBack'] is True and p['cloudObjectDeleted'] is False and p['verifiedAt']
                pruned.append(archive.name)
        except (Exception,):
            # Preserve failed/unknown history. It cannot count as usable proof.
            unverified+=1
    return {'verified_local_count':len(valid),'verified_pruned_count':len(pruned),'unverified_history_count':unverified}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');args=p.parse_args()
    assert os.geteuid()==0 and Path('/etc/machine-id').read_text().strip()==MACHINE
    profile=json.loads(Path('/etc/zhuojian/runtime.json').read_bytes())
    assert profile['organizationId']==ORG and profile['runtimeId']=='aifabei-hk-01'
    wrapper=Path('/usr/local/sbin/zhuojian-online-backup').read_text().split('"')
    import sys
    sys.path.insert(0,str(Path(wrapper[3]).parent));import runtime_backup_oss as t
    plan_path=Path('/etc/zhuojian/backup-online-plan.json');plan_raw=regular(plan_path,True);plan=json.loads(plan_raw)
    pins={'plan_sha256':hashlib.sha256(plan_raw).hexdigest(),'wrappers':{n:hashlib.sha256(regular(Path('/usr/local/sbin')/n)).hexdigest() for n in ['zhuojian-online-backup','zhuojian-backup-oss','zhuojian-recovery-evidence']}}
    gates={};scope=t.BackupScope(profile)
    for slug in plan['applications']:
        gate=point_gate(Path('/srv/zhuojian/backups')/slug,scope,slug,t)
        assert gate['verified_local_count']>=2 and gate['verified_pruned_count']>=1,'two verified local points and a verified third-point prune required'
        gates[slug]=gate
    assert len(gates)==9 and not command('systemctl','is-active','zhuojian-backup.service',check=False).stdout.strip() in {'active','activating'}
    rendered=units();paths={Path('/etc/systemd/system')/n:s.encode() for n,s in rendered.items()}
    assert all(not x.exists() and not x.is_symlink() for x in [ROOT,*paths])
    before_enabled=command('systemctl','is-enabled',OLD,check=False).stdout.strip()
    before_active=command('systemctl','is-active',OLD,check=False).stdout.strip()
    if args.apply:
        with t.publication_lock(Path('/run/lock/zhuojian-runtime-admin.lock')):
            assert plan_path.read_bytes()==plan_raw
            ROOT.mkdir(mode=0o700)
            t.atomic_json(ROOT/'pins.json',pins)
            atomic(ROOT/'preflight.py',PREFLIGHT.encode(),0o500)
            atomic(ROOT/'previous-timer-state.json',json.dumps({'enabled':before_enabled,'active':before_active}).encode(),0o600)
            for path,raw in paths.items():atomic(path,raw,0o644)
            command('systemd-analyze','verify',*(str(x) for x in paths))
            command('/usr/bin/python3',str(ROOT/'preflight.py'))
            command('systemctl','daemon-reload')
            command('systemctl','disable','--now',OLD)
            try:
                assert command('systemctl','is-active','zhuojian-backup.service',check=False).stdout.strip() not in {'active','activating'}
                command('systemctl','enable','--now',NEW)
            except BaseException:
                command('systemctl','disable','--now',NEW,check=False)
                # Old native jobs stop business apps. Never reactivate them as
                # an automatic failure fallback for the online-only contract.
                raise
    print(json.dumps({'observed_at':dt.datetime.now(dt.timezone.utc).isoformat(),'applied':args.apply,'gates':gates,'units':{n:hashlib.sha256(v.encode()).hexdigest() for n,v in rendered.items()},'pins':pins,'previous_timer_enabled':before_enabled,'previous_timer_active':before_active,'business_services_stopped':False,'legacy_units_or_wrappers_modified':False,'old_timer_disabled_only':args.apply}))


if __name__=='__main__':main()
