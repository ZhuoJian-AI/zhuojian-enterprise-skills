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
