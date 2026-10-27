import importlib.util
import json
import os
from pathlib import Path
import sys
import pytest

CORE=Path(__file__).resolve().parents[2]/'skills/core/zhuojian-subsystem-builder'
sys.path.insert(0,str(CORE/'tests'))
sys.path.insert(0,str(CORE/'scripts'))
import runtime_backup_oss as transport
from test_runtime_online_retention import seed
from test_runtime_backup_oss import Backend

PATH=Path(__file__).resolve().parents[2]/'scripts/maintenance/install_alphabet_online_schedule_20261028.py'
spec=importlib.util.spec_from_file_location('alphabet_online_schedule',PATH)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_online_primary_and_windows_secondary_are_separate():
    units=module.units();primary=units['zhuojian-online-backup.service']
    assert 'ExecStart=/usr/local/sbin/zhuojian-online-backup --publish --verify-restore all' in primary
    assert 'backup-all' not in primary and 'gate_backup.py' not in primary
    assert 'OnSuccess=zhuojian-backup-windows-export.service' in primary
    assert 'windows' in units['zhuojian-backup-windows-export.service']
    assert 'RandomizedDelaySec=15m' in units['zhuojian-online-backup.timer']
    compile(module.PREFLIGHT,'<isolated-preflight>','exec')
    assert 'windows-verified.json' not in module.PREFLIGHT and '5*1024**3' in module.PREFLIGHT


def point(tmp_path,hour):
    scope,path=seed(tmp_path,Backend(),hour)
    meta=json.loads(path.with_suffix('.gz.json').read_text());meta.update(archive=path.name,applicationSlug='example')
    transport.atomic_json(path.with_suffix('.gz.json'),meta)
    remote=json.loads(path.with_suffix('.gz.remote.json').read_text());remote.update(fullReadbackAt='2026-10-27T16:00:00+00:00',offServer=True)
    transport.atomic_json(path.with_suffix('.gz.remote.json'),remote)
    return scope,path,meta,remote


def test_failed_history_does_not_block_two_valid_points_and_prune_is_bound(tmp_path):
    scope,old,_,remote=point(tmp_path,7)
    _,a,_,_=point(tmp_path,8);_,b,_,_=point(tmp_path,9)
    old.unlink()
    receipt={'archive':old.name,'sha256':remote['sha256'],'versionId':remote['versionId'],'bytes':remote['sizeBytes'],
             'isolatedRestoreMatched':True,'exactRemoteVersionReadBack':True,'cloudObjectDeleted':False,'verifiedAt':'2026-10-27T16:00:00+00:00'}
    transport.atomic_json(old.with_suffix('.gz.pruned.json'),receipt)
    _,unknown,_,_=point(tmp_path,6);unknown.with_suffix('.gz.restore.json').unlink()
    result=module.point_gate(old.parent,scope,'example',transport)
    assert result=={'verified_local_count':2,'verified_pruned_count':1,'unverified_history_count':1}
    receipt['sha256']='a'*64;transport.atomic_json(old.with_suffix('.gz.pruned.json'),receipt)
    assert module.point_gate(old.parent,scope,'example',transport)['verified_pruned_count']==0
    a.write_bytes(b'changed')
    assert module.point_gate(old.parent,scope,'example',transport)['verified_local_count']==1


@pytest.mark.skipif(os.name=='nt',reason='native symlink ownership check')
def test_symlink_is_not_a_verified_local_recovery_point(tmp_path):
    scope,a,_,_=point(tmp_path,8);_,b,_,_=point(tmp_path,9)
    a.unlink();a.symlink_to(b)
    assert module.point_gate(a.parent,scope,'example',transport)['verified_local_count']==1
