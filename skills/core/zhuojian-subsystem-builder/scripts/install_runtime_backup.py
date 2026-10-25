#!/usr/bin/env python3
"""Install the root-only OSS backup CLI; does not configure cloud access or timers."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import subprocess
import tempfile


MARKER = 'zhuojian-runtime-backup-tools/v1'
DEPENDENCY = 'oss2==2.19.1'
WRAPPER_HEADER = '#!/bin/sh\n# ' + MARKER + '\n'


def owned_directory(path):
    if path.is_symlink():
        raise RuntimeError('refusing a symlink installation directory')
    if not path.exists():
        path.mkdir(mode=0o700)
    info = path.stat()
    if not stat.S_ISDIR(info.st_mode) or (os.name == 'posix' and (info.st_uid != 0 or stat.S_IMODE(info.st_mode) & 0o077)):
        raise RuntimeError('installation directory must be private and root owned')


def protected_file(path):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or (os.name == 'posix' and (info.st_uid != 0 or stat.S_IMODE(info.st_mode) & 0o022)):
        raise RuntimeError('refusing an unsafe installation file')


def atomic_write(path, content, mode):
    fd, name = tempfile.mkstemp(prefix='.backup-install-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def run(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    if result.returncode:
        raise RuntimeError('backup dependency installation or import check failed; previous CLI remains installed')


def install(source, root=Path('/opt/zhuojian/backup-tools'), wrapper=Path('/usr/local/sbin/zhuojian-backup-oss'), runner=run):
    if source.is_symlink() or not source.is_file():
        raise RuntimeError('backup source must be a regular file')
    if root.exists() or root.is_symlink():
        owned_directory(root)
        marker = root / '.managed'
        if not marker.is_file():
            raise RuntimeError('refusing to adopt an unknown installation directory')
        protected_file(marker)
        if marker.read_text() != MARKER:
            raise RuntimeError('unknown backup tools installation marker')
    else:
        # /opt/zhuojian belongs to initialized Runtime, not this installer.
        if root.parent.is_symlink() or not root.parent.is_dir():
            raise RuntimeError('initialize the Runtime installation parent first')
        owned_directory(root)
        atomic_write(root / '.managed', MARKER.encode(), 0o600)
    if wrapper.exists() or wrapper.is_symlink():
        protected_file(wrapper)
        text = wrapper.read_text()
        prefix = WRAPPER_HEADER + 'exec "' + root.as_posix() + '/'
        if not text.startswith(prefix) or not text.endswith('/runtime_backup_oss.py" "$@"\n'):
            raise RuntimeError('refusing to overwrite an unknown backup CLI wrapper')
    data = source.read_bytes()
    digest = hashlib.sha256(data + DEPENDENCY.encode()).hexdigest()
    release = root / digest
    owned_directory(release)
    script = release / 'runtime_backup_oss.py'
    if script.exists() or script.is_symlink():
        protected_file(script)
        if script.read_bytes() != data:
            raise RuntimeError('existing backup release content differs')
    else:
        atomic_write(script, data, 0o600)
    python = release / 'venv/bin/python'
    if not python.exists():
        runner(['python3', '-m', 'venv', str(release / 'venv')])
    runner([str(python), '-m', 'pip', 'install', '--disable-pip-version-check', DEPENDENCY])
    runner([str(python), '-c', 'import oss2'])
    content = WRAPPER_HEADER + f'exec "{python.as_posix()}" "{script.as_posix()}" "$@"\n'
    atomic_write(wrapper, content.encode(), 0o750)
    return {'installed': True, 'cloudConfigured': False, 'scheduled': False, 'release': digest}


if __name__ == '__main__':
    import json
    try:
        if os.name != 'posix' or os.geteuid() != 0:
            raise RuntimeError('installer requires the authorized GNU/Linux Runtime root environment')
        # Serialize with Runtime upgrades and other installers.
        import runtime_backup_oss
        with runtime_backup_oss.publication_lock(Path('/run/lock/zhuojian-runtime-admin.lock')):
            print(json.dumps(install(Path(__file__).with_name('runtime_backup_oss.py'))))
    except Exception as exc:
        print(json.dumps({'installed': False, 'error': str(exc)}))
        raise SystemExit(2)
