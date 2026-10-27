#!/usr/bin/env python3
"""Narrow reviewed compatibility patch for Alphabet's existing Windows exporter.

Does not run backup/export/prune, touch Windows, change ACKs, or stop services.
Existing ACKs remain genuine. Legacy archive deletion is disabled; the online
transport alone owns verified v3 retention and preserves all schema2 history.
"""
import argparse
import ast
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
    # Insert after imports/constants, before the first top-level function. The
    # exporter has plain(); the separately pinned policy uses another first def.
    first=next((n for n in ast.parse(target).body if isinstance(n,ast.FunctionDef)),None)
    if first is None:raise RuntimeError('unknown exporter/policy definition layout')
    lines=target.splitlines(keepends=True)
    offset=sum(len(line) for line in lines[:first.lineno-1])
    target=target[:offset]+PREDICATE+'\n'+target[offset:]
    compile(target,'<reviewed-alphabet-backup-compat>','exec')
    return target


def render_policy(source):
    target=render(source)
    node=next((n for n in ast.parse(target).body if isinstance(n,ast.FunctionDef) and n.name=='prune_acknowledged'),None)
    if node is None:raise RuntimeError('unexpected legacy archive retention implementation')
    lines=target.splitlines(keepends=True)
    replacement='''def prune_acknowledged():
    # ACK acceptance is unchanged; never let the old Windows policy delete
    # legacy archives or compete with exact-version v3 cloud retention.
    load_config()
    controlled_directories()
    result = {"observed_at": now(), "deleted_windows_verified_old_archives": [],
              "retained_current_and_previous": True, "legacy_history_preserved": True,
              "retention_owner": "verified_online_v3_transport",
              "original_seven_or_source_touched": False}
    atomic(ROOT / "last-prune.json", result)
    return result
'''
    target=''.join(lines[:node.lineno-1])+replacement+''.join(lines[node.end_lineno:])
    compile(target,'<reviewed-alphabet-backup-policy>','exec')
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
        renderer=render_policy if name=='backup_policy.py' else render
        changes[name]=(original,renderer(original.decode()).encode(),stat.S_IMODE(info.st_mode))
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
