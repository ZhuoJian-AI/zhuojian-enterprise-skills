import importlib.util
from pathlib import Path

import pytest


SPEC = importlib.util.spec_from_file_location('install_runtime_backup', Path(__file__).parents[1] / 'scripts/install_runtime_backup.py')
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


def test_install_switches_wrapper_only_after_dependency_check(tmp_path):
    root = tmp_path / 'managed'
    wrapper = tmp_path / 'backup-cli'
    source = tmp_path / 'source.py'
    source.write_text('print("backup")')
    calls = []
    installer.install(source, root, wrapper, runner=lambda command: calls.append(command))
    before = wrapper.read_bytes()
    assert len(calls) == 3
    source.write_text('print("new backup")')
    def fail(command):
        raise RuntimeError('installation failed')
    with pytest.raises(RuntimeError):
        installer.install(source, root, wrapper, runner=fail)
    assert wrapper.read_bytes() == before
    assert 'cloudConfigured' in installer.install(source, root, wrapper, runner=lambda command: None)


def test_install_refuses_unknown_directory_and_wrapper(tmp_path):
    root = tmp_path / 'managed'
    root.mkdir(mode=0o700)
    source = tmp_path / 'source.py'
    source.write_text('fixture')
    wrapper = tmp_path / 'backup-cli'
    with pytest.raises(RuntimeError, match='unknown installation'):
        installer.install(source, root, wrapper, runner=lambda command: None)
    (root / '.managed').write_text(installer.MARKER)
    (root / '.managed').chmod(0o600)
    wrapper.write_text('another application')
    with pytest.raises(RuntimeError, match='unknown backup CLI'):
        installer.install(source, root, wrapper, runner=lambda command: None)


def test_companion_commands_switch_together_after_all_validation(tmp_path):
    root=tmp_path/'managed';wrapper=tmp_path/'backup-cli';source=tmp_path/'runtime_backup_oss.py'
    source.write_text('transport_source')
    (tmp_path/'runtime_online_backup.py').write_text('online_source')
    (tmp_path/'runtime_recovery_evidence.py').write_text('observer_source')
    result=installer.install(source,root,wrapper,runner=lambda command:None)
    online=tmp_path/'zhuojian-online-backup';observer=tmp_path/'zhuojian-recovery-evidence'
    before={p:p.read_bytes() for p in [wrapper,online,observer]}
    assert all(result['release'] in p.read_text() for p in before)
    (tmp_path/'runtime_online_backup.py').write_text('new_online_source')
    def fail(command):raise RuntimeError('dependency failed')
    with pytest.raises(RuntimeError):installer.install(source,root,wrapper,runner=fail)
    assert all(p.read_bytes()==content for p,content in before.items())
    observer.write_text('unrelated observer command')
    with pytest.raises(RuntimeError,match='unknown backup CLI'):
        installer.install(source,root,wrapper,runner=lambda command:None)
    assert wrapper.read_bytes()==before[wrapper] and online.read_bytes()==before[online]


def test_missing_ensurepip_installs_only_into_private_environment(tmp_path,monkeypatch):
    root=tmp_path/'managed';wrapper=tmp_path/'backup-cli';source=tmp_path/'source.py';source.write_text('fixture')
    monkeypatch.setattr(installer.importlib.util,'find_spec',lambda name:None)
    calls=[]
    installer.install(source,root,wrapper,runner=lambda command:calls.append(command),index_url='https://mirrors.aliyun.com/pypi/simple')
    assert '--without-pip' in calls[0]
    install=calls[1]
    assert '--python' in install and str(root) in install[install.index('--python')+1]
    assert '--index-url' in install and 'https://mirrors.aliyun.com/pypi/simple' in install
    assert '--break-system-packages' not in install
