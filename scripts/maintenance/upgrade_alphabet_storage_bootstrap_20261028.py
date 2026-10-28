#!/usr/bin/env python3
"""Upgrade only Alphabet's reviewed daily preflight for scoped STS adoption.

Dry-run by default. This does not install tools, change credentials, start a
backup, alter timers or restart business services. Install the preflight before
the new tool generation, then configure STS only after the new generation passes.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import inspect
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import tempfile

import install_alphabet_online_schedule_20261028 as original

ROOT = original.ROOT
MACHINE = original.MACHINE
MARKER = 'alphabet-storage-bootstrap-preflight/v1'
OLD_PREFLIGHT_SHA = '656face6e3a4fcaec747cee93bf77bfccf404dad4ed32d95989e5f55be272a1a'
OLD_PINS_SHA = 'b33bfe4d6aeb1fb4da557da8391004a836dea72c594adde91f12d390f43f7c92'
TIMER_SHA = 'ce0f86bd09b1830a33d393e4d95133508efcad8d0f8cd0ebc4f830874d0d4f89'
SERVICE_SHA = 'e4a3c0ef98d58cfdec6e1463b15f906b58f4d75c963a1fe2477a25446c1d75ed'
OLD_RELEASE = 'a6de832052f14ef3417b0575ed366c8a3c9553a0941eaab716c5e90d627221ab'
NEW_RELEASE = '7ec8fd487f3f5dc870515f4a44cff5626b4fe9884d0ccd9baa76fa72b40a6632'
NEW_MODULES = {
    'runtime_backup_oss.py': '5b0671a27252c6bdd1d07b671385841299d52b3d65e20ec471b326f2e9a3698f',
    'runtime_online_backup.py': 'b183ba53ef05543afbc52b17005320c9212ac3e186ad591d52f03e6229d977fa',
    'runtime_recovery_evidence.py': '2507d098a57ebfcac343357ab3daf370aca9863f7806f6e0017db2af9bd38fdc',
    'runtime_storage_bootstrap.py': 'a1619f120b3ec731011aee6b4ba49027e61a9833eefba16668e37b1aa5ed9d0e',
    'runtime_backup_plan.py': '83a5bd2d75057196a4d05315ea92c32c1206206f9ba9a1bb350232a1062de451',
}
RUNTIME_ADMIN_SHA = '90b00e3edf1d7c1528e0054919ff9a830a77daa9b247318f53b31c1da37b7aea'
PLAN_BASELINE = {
    'identitySha256': 'b9d35b39b82adece9e3df54951d75eb0bc9b4e8aae22cdc5743966e5aaf10d0c',
    'applications': {
        'daoxun-data-center': '750efe5e75bac859c84c44f02bc68b0ace1421d41d0be9f0aaf384159cf09c99',
        'enterprise-culture': '8728522b0a2cdfe431e84ee54ed514fef88058848db77215b20f4db56406ad94',
        'enterprise-notifications': '959388536f472bf8675c0f4d116b29207a8f8f740751c64fddb6e8bf368119ec',
        'garment-production-collaboration': 'b26dfb3e53f941a215e9247c5b3490d4cc190a98c5e45157f011b92accb80d20',
        'goods-movement-dashboard': 'dac3292b16733cafd81ee0eff918893d8742f35c2b62752398da7373d7bb295b',
        'inspiration-pattern-library': '5f72077fae57458bdc4b1ba8fd2e908a9a046b7ded18ccbb9e769ab5558b55d9',
        'nas-files': 'ebf4a62ef9eea33077b50757c4b158d72043ab8f25399d153d0baf3c3bde3088',
        'pattern-technology-hub': 'a881334d179952ebaf7d85ef1a6443a9efda9cc559c691e1632af703deef2009',
        'product-360': '529e9f154cd904073ab831746bcebd60318b4209b60b4ba19068fcd73cd773f5',
    },
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_plan(plan, baseline):
    """Keep every reviewed old item; allow only bounded helper-owned additions."""
    canonical = lambda value: json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    identity = {k: v for k, v in plan.items() if k != 'applications'}
    if hashlib.sha256(canonical(identity)).hexdigest() != baseline['identitySha256']:
        raise ValueError('reviewed plan identity changed')
    applications = plan.get('applications')
    if not isinstance(applications, dict) or not len(baseline['applications']) <= len(applications) <= 256:
        raise ValueError('reviewed applications are missing or unbounded')
    for slug, expected in baseline['applications'].items():
        if slug not in applications or hashlib.sha256(canonical(applications[slug])).hexdigest() != expected:
            raise ValueError('reviewed application plan changed')
    for slug, app in applications.items():
        if slug in baseline['applications']:
            continue
        if not isinstance(slug, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,62}', slug) or not isinstance(app, dict):
            raise ValueError('invalid enrolled application')
        if set(app) - {'name', 'project_id', 'initialProtectionRequired', 'primary_sqlite', 'enrollment'}:
            raise ValueError('new application requires manual plan review')
        if app.get('name') != slug or app.get('project_id') is not None:
            raise ValueError('invalid enrolled identity')
        if 'initialProtectionRequired' in app and type(app['initialProtectionRequired']) is not bool:
            raise ValueError('invalid initial protection state')
        enrollment = app.get('enrollment')
        if not isinstance(enrollment, dict) or enrollment.get('managedBy') != 'zhuojian-runtime-backup-enrollment/v1':
            raise ValueError('unowned backup enrollment')
        if set(enrollment) - {'managedBy', 'status', 'reason', 'primary_sqlite', 'database_kind', 'method', 'observedCommit', 'observedAt'}:
            raise ValueError('unreviewed enrollment fields')
        if enrollment.get('status') not in {'ready', 'pending'}:
            raise ValueError('invalid enrollment state')
        for name in ('primary_sqlite',):
            for value in (app.get(name), enrollment.get(name)):
                if value is not None:
                    path = PurePosixPath(value) if isinstance(value, str) else None
                    if path is None or not value.startswith('/data/') or str(path) != value or '..' in path.parts:
                        raise ValueError('enrolled database is outside the fixed data mount')
        if enrollment['status'] == 'ready' and (
            not app.get('primary_sqlite') or enrollment.get('primary_sqlite') != app['primary_sqlite']
            or enrollment.get('database_kind') != 'sqlite'
            or enrollment.get('method') != 'sqlite_magic_and_runtime_mount'
        ):
            raise ValueError('ready enrollment has no supported adapter')
        commit = enrollment.get('observedCommit')
        if commit is not None and (not isinstance(commit, str) or not re.fullmatch(r'[a-f0-9]{40}', commit)):
            raise ValueError('invalid enrollment commit')


def wrapper_bytes(release, module):
    directory = '/opt/zhuojian/backup-tools/' + release
    return ('#!/bin/sh\n# zhuojian-runtime-backup-tools/v1\n'
            f'exec "{directory}/venv/bin/python" "{directory}/{module}" "$@"\n').encode()


def verify_generation(pins, profile, reader):
    for label, items in pins['generations'].items():
        try:
            for name, expected in items['wrappers'].items():
                if hashlib.sha256(reader(Path('/usr/local/sbin') / name, private=False)).hexdigest() != expected:
                    raise ValueError('wrapper mismatch')
            for name, expected in items['modules'].items():
                if hashlib.sha256(reader(Path(name), private=True)).hexdigest() != expected:
                    raise ValueError('module mismatch')
        except (OSError, ValueError, RuntimeError):
            continue
        if (profile.get('backupStorage') or {}).get('credentialProvider') == 'platform-sts-v1' and label != 'platform-sts-v1':
            raise ValueError('STS requires the renewable SDK generation')
        return label
    raise ValueError('unreviewed or mixed backup tool generation')


def new_pins(old):
    modules = {f'/opt/zhuojian/backup-tools/{NEW_RELEASE}/{name}': sha for name, sha in NEW_MODULES.items()}
    modules.update({
        '/usr/local/lib/zhuojian/runtime_admin.py': RUNTIME_ADMIN_SHA,
        '/usr/local/lib/zhuojian/runtime_backup_plan.py': NEW_MODULES['runtime_backup_plan.py'],
    })
    wrappers = {f'zhuojian-{name}': digest(wrapper_bytes(NEW_RELEASE, module)) for name, module in [
        ('online-backup', 'runtime_online_backup.py'), ('backup-oss', 'runtime_backup_oss.py'),
        ('recovery-evidence', 'runtime_recovery_evidence.py'), ('storage-bootstrap', 'runtime_storage_bootstrap.py'),
    ]}
    return {**old, 'managedBy': MARKER, 'planBaseline': PLAN_BASELINE,
            'generations': {'legacy-static': {'wrappers': old['wrappers'], 'modules': old['modules']},
                            'platform-sts-v1': {'wrappers': wrappers, 'modules': modules}}}


def render_preflight():
    windows = original.PREFLIGHT.split("if len(sys.argv)>1 and sys.argv[1]=='windows':", 1)[1]
    return ('# ' + MARKER + '\n'
        'import hashlib,json,os,shutil,stat,sys,re\nfrom pathlib import Path,PurePosixPath\n'
        'ROOT=Path(__file__).parent\n' + inspect.getsource(validate_plan) + inspect.getsource(regular) + inspect.getsource(verify_generation) + '''
def private(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and not p.is_symlink() and s.st_mode&0o077==0
 return p.read_bytes()
assert os.geteuid()==0 and Path('/etc/machine-id').read_text().strip()==''' + repr(MACHINE) + '''
pins=json.loads(private(ROOT/'pins.json'))
profile=json.loads(Path('/etc/zhuojian/runtime.json').read_bytes())
verify_generation(pins,profile,regular)
plan=json.loads(private(Path('/etc/zhuojian/backup-online-plan.json')))
validate_plan(plan,pins['planBaseline'])
assert plan['organizationId']==profile['organizationId']==''' + repr(original.ORG) + ''' and plan['runtimeId']==profile['runtimeId']=='aifabei-hk-01' and plan['environment']==profile['environment']=='staging'
assert shutil.disk_usage('/srv/zhuojian').free>=5*1024**3
if len(sys.argv)>1 and sys.argv[1]=='windows':''' + windows).encode()


def regular(path, *, private=False):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_uid != 0 or info.st_mode & (0o077 if private else 0o022):
        raise RuntimeError('unsafe owned upgrade file')
    return path.read_bytes()


def atomic(path, raw, mode):
    fd, temporary = tempfile.mkstemp(prefix='.storage-preflight-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(raw); handle.flush(); os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary)


def commit_files(payloads):
    before = {path: (regular(path, private=True), stat.S_IMODE(path.stat().st_mode)) for path in payloads}
    try:
        for path, (raw, mode) in payloads.items():
            if regular(path, private=True) != before[path][0]:
                raise RuntimeError('upgrade source changed')
            atomic(path, raw, mode)
    except BaseException:
        conflict = False
        for path, (raw, _mode) in reversed(list(payloads.items())):
            try:
                current = regular(path, private=True)
            except (OSError, RuntimeError):
                conflict = True
                continue
            if current == before[path][0]:
                continue
            if current != raw:
                conflict = True; continue
            atomic(path, *before[path])
        if conflict:
            raise RuntimeError('upgrade rollback conflict') from None
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    if os.geteuid() != 0 or Path('/etc/machine-id').read_text().strip() != MACHINE:
        raise RuntimeError('wrong host identity')
    import fcntl
    with open('/run/lock/zhuojian-runtime-admin.lock', 'a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for name, expected in [('timer', TIMER_SHA), ('service', SERVICE_SHA)]:
            if digest(regular(Path('/etc/systemd/system/zhuojian-online-backup.' + name))) != expected:
                raise RuntimeError('reviewed daily unit changed')
        active = subprocess.run(['systemctl', 'is-active', 'zhuojian-online-backup.service'], capture_output=True, text=True, timeout=15).stdout.strip()
        if active in {'active', 'activating', 'reloading', 'deactivating'}:
            raise RuntimeError('existing online backup is running')
        preflight, pins = ROOT / 'preflight.py', ROOT / 'pins.json'
        old_preflight, old_pins = regular(preflight, private=True), regular(pins, private=True)
        if digest(old_preflight) != OLD_PREFLIGHT_SHA or digest(old_pins) != OLD_PINS_SHA:
            raise RuntimeError('reviewed previous preflight changed; inspect before retrying')
        original_pins = json.loads(old_pins)
        plan_raw = regular(Path('/etc/zhuojian/backup-online-plan.json'), private=True)
        plan = json.loads(plan_raw)
        validate_plan(plan, PLAN_BASELINE)
        for name, expected in original_pins['wrappers'].items():
            if digest(regular(Path('/usr/local/sbin') / name)) != expected:
                raise RuntimeError('upgrade preflight before replacing the old tools')
        for name, expected in original_pins['modules'].items():
            if digest(regular(Path(name), private=True)) != expected:
                raise RuntimeError('original pinned module changed')
        payload = json.dumps(new_pins(original_pins), sort_keys=True, separators=(',', ':')).encode()
        rendered = render_preflight()
        compile(rendered, '<reviewed-storage-preflight>', 'exec')
        if args.apply:
            backup = ROOT / 'before-storage-bootstrap-v1'
            if backup.exists() or backup.is_symlink():
                raise RuntimeError('upgrade snapshot already exists; inspect previous result')
            backup.mkdir(mode=0o700)
            atomic(backup / 'preflight.py', old_preflight, 0o500)
            atomic(backup / 'pins.json', old_pins, 0o600)
            atomic(backup / 'backup-online-plan.json', plan_raw, 0o600)
            commit_files({pins: (payload, 0o600), preflight: (rendered, 0o500)})
        print(json.dumps({'applied': args.apply, 'preflightSha256': digest(rendered), 'pinsSha256': digest(payload),
                          'oldPlanItemsPreserved': len(PLAN_BASELINE['applications']), 'newToolRelease': NEW_RELEASE,
                          'credentialsChanged': False, 'timerChanged': False, 'businessServicesRestarted': False}))


if __name__ == '__main__':
    main()
