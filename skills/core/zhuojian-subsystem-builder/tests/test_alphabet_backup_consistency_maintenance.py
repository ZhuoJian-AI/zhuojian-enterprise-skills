import importlib.util
from pathlib import Path
import pytest

PATH=Path(__file__).parents[4]/'scripts/maintenance/upgrade_alphabet_backup_consistency_20261027.py'
SPEC=importlib.util.spec_from_file_location('alphabet_consistency_maintenance',PATH)
module=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(module)


def test_compatibility_preserves_old_points_and_requires_explicit_online_checks():
    source='import json\n\ndef plain(path):\n    return path\n\ndef inspect(metadata):\n    assert metadata["consistentOfflineSnapshot"] is True\n'
    changed=module.render(source);scope={};exec(compile(changed,'<test>','exec'),scope)
    accept=scope['accepted_consistency']
    assert accept({'schemaVersion':2,'consistentOfflineSnapshot':True})
    assert not accept({'schemaVersion':3,'consistentOfflineSnapshot':True})
    metadata={'schemaVersion':3,'consistentOfflineSnapshot':False,'consistency':{'method':'sqlite_online_backup','businessServicesStopped':False,'databaseIntegrityVerified':True,'fileHashesVerified':True,'referencesVerified':True,'manifestSha256':'a'*64}}
    assert accept(metadata)
    metadata['consistency']['referencesVerified']=False
    assert not accept(metadata)
    assert 'def inspect(metadata):' in changed
    with pytest.raises(RuntimeError):module.render(changed)


def test_policy_without_exporter_plain_helper_is_supported():
    source='import json\nMACHINE="fixed"\n\ndef now():\n    return "time"\n\ndef inspect(metadata):\n    assert metadata["consistentOfflineSnapshot"] is True\n'
    changed=module.render(source)
    assert changed.index('MACHINE=')<changed.index('def accepted_consistency(')<changed.index('def now(')


def test_ack_policy_keeps_history_and_does_not_forge_acknowledgement():
    source='import json\n\ndef now():\n    return "time"\n\ndef inspect(metadata):\n    assert metadata["consistentOfflineSnapshot"] is True\n\ndef prune_acknowledged():\n    dangerous.unlink()\n'
    target=module.render_policy(source)
    assert 'dangerous.unlink()' not in target and 'legacy_history_preserved' in target
    assert 'windows-verified.json' not in target and 'verified_online_v3_transport' in target
