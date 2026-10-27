#!/usr/bin/env python3
"""Narrow reviewed compatibility patch for Alphabet's existing Windows exporter.

Does not run backup/export/prune, touch Windows, change ACKs, or stop services.
The two files remain identical except for an explicit online-consistency check.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile

MACHINE='24b1027fbbb34fe080910773ec63ebc9'
ROOT=Path('/etc/zhuojian/integrations/alphabet-offsite-backup-20261025')
KNOWN={'backup_policy.py':'99de890662648366cdc26375c6c551865608cc6f81f5d4068102ff4eb3d6dcfb',
       'export_latest.py':None}
CHECK='assert metadata["consistentOfflineSnapshot"] is True'
PREDICATE='''\n\ndef accepted_consistency(metadata):
    """Keep legacy archives; accept verified online captures without claiming offline."""
    if metadata.get("schemaVersion") == 2:
        return metadata.get("consistentOfflineSnapshot") is True
    proof = metadata.get("consistency") or {}
    return (metadata.get("schemaVersion") == 3
            and metadata.get("consistentOfflineSnapshot") is False
            and proof.get("method") == "sqlite_online_backup"
            and proof.get("businessServicesStopped") is False
            and all(proof.get(k) is True for k in (
                "databaseIntegrityVerified", "fileHashesVerified", "referencesVerified"))
            and isinstance(proof.get("manifestSha256"), str)
            and len(proof["manifestSha256"]) == 64
            and all(c in "0123456789abcdef" for c in proof["manifestSha256"]))
'''


def render(source):
    if source.count(CHECK)!=1 or 'def accepted_consistency(' in source:
        raise RuntimeError('unexpected existing Alphabet backup compatibility source')
    target=source.replace(CHECK,'assert accepted_consistency(metadata)')
    # Both installed files define plain() before any execution entrypoint.
    marker='\ndef plain(path):'
    if target.count(marker)!=1:raise RuntimeError('unknown exporter/policy definition layout')
    target=target.replace(marker,PREDICATE+marker,1)
    compile(target,'<reviewed-alphabet-backup-compat>','exec')
    return target


def atomic(path,data,mode):
    fd,name=tempfile.mkstemp(prefix='.consistency-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as h:h.write(data);h.flush();os.fsync(h.fileno())
        os.chmod(name,mode);os.replace(name,path)
    finally:
        with contextlib.suppress(FileNotFoundError):os.unlink(name)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--exporter-sha256',required=True);parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if os.geteuid()!=0 or Path('/etc/machine-id').read_text().strip()!=MACHINE:raise RuntimeError('unexpected host')
    profile=json.loads(Path('/etc/zhuojian/runtime.json').read_text())
    assert profile['runtimeId']=='aifabei-hk-01' and profile['organizationId']=='65130a23-b05e-4026-9615-761ab2d4193c'
    known={**KNOWN,'export_latest.py':args.exporter_sha256};changes={}
    for name,expected in known.items():
        p=ROOT/name;info=p.lstat()
        assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and not p.is_symlink() and info.st_mode&0o022==0
        original=p.read_bytes();assert hashlib.sha256(original).hexdigest()==expected
        changes[name]=(original,render(original.decode()).encode(),stat.S_IMODE(info.st_mode))
    if args.apply:
        spec=importlib.util.spec_from_file_location('alphabet_backup_policy',ROOT/'backup_policy.py')
        policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
        with policy.locked():
            for name,(before,after,mode) in changes.items():
                assert (ROOT/name).read_bytes()==before
                backup=ROOT/(name+'.pre-online-20261027')
                assert not backup.exists() and not backup.is_symlink()
                fd=os.open(backup,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                with os.fdopen(fd,'wb') as h:h.write(before);h.flush();os.fsync(h.fileno())
            installed=[]
            try:
                for name,(before,after,mode) in changes.items():
                    assert (ROOT/name).read_bytes()==before
                    atomic(ROOT/name,after,mode);installed.append(name)
            except BaseException:
                for name in reversed(installed):
                    before,after,mode=changes[name]
                    if (ROOT/name).read_bytes()==after:atomic(ROOT/name,before,mode)
                raise
    print(json.dumps({'applied':args.apply,'changes':{name:{'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest()} for name,(before,after,mode) in changes.items()},'backup_or_export_triggered':False}))


if __name__=='__main__':main()
