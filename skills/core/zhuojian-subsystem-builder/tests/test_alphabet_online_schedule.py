import importlib.util
from pathlib import Path

PATH=Path(__file__).parents[4]/'scripts/maintenance/install_alphabet_online_schedule_20261028.py'
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
