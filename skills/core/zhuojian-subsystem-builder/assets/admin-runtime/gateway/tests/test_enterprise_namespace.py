from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from zhuojian_storage_gateway.app import create_app
from zhuojian_storage_gateway.config import ConfigurationError, GatewaySettings, load_oss_credentials
from zhuojian_storage_gateway.cli import _assert_outside_prefix_denied, GatewayProbeError
from zhuojian_storage_gateway.config import OssCredentials
from zhuojian_storage_gateway.registry import CredentialRegistry
from test_gateway import FakeStorageAdapter, _read_token, _auth


def profile(tmp_path: Path, monkeypatch, organization: str, storage=None):
    path=tmp_path/'runtime.json'
    value={'organizationId':organization,'environment':'staging'}
    if storage is not None:value['objectStorage']=storage
    path.write_text(json.dumps(value),encoding='utf-8')
    path.chmod(0o600)
    monkeypatch.setenv('GATEWAY_RUNTIME_PROFILE',str(path))
    return path


def test_new_gateway_derives_shared_scope_and_old_gateway_preserves_legacy(tmp_path,monkeypatch):
    organization='11111111-1111-4111-8111-111111111111'
    profile(tmp_path,monkeypatch,organization)
    settings=GatewaySettings.from_environment()
    assert settings.root_prefix == f'enterprises/{organization}/staging/apps'
    assert settings.namespace_mode == 'enterprise-v1'
    profile(tmp_path,monkeypatch,organization,{'bucket':'legacy-private','rootPrefix':'apps'})
    assert GatewaySettings.from_environment().root_prefix == 'apps'


requires_posix_root = pytest.mark.skipif(
    os.name != "posix" or getattr(os, "geteuid", lambda: -1)() != 0,
    reason="actual root-owned POSIX file metadata is required",
)


@requires_posix_root
@pytest.mark.parametrize("mode", [0o600, 0o640, 0o644])
def test_existing_runtime_profile_permissions_work_for_shared_and_legacy(tmp_path, monkeypatch, mode):
    organization = "11111111-1111-4111-8111-111111111111"
    for storage, prefix in [(None, f"enterprises/{organization}/staging/apps"),
                            ({"bucket": "legacy-private", "rootPrefix": "apps"}, "apps")]:
        path = profile(tmp_path, monkeypatch, organization, storage)
        path.chmod(mode)
        assert path.stat().st_uid == 0
        assert GatewaySettings.from_environment().root_prefix == prefix


@requires_posix_root
@pytest.mark.parametrize("mode", [0o620, 0o602, 0o622, 0o666])
def test_runtime_profile_rejects_group_or_other_writers(tmp_path, monkeypatch, mode):
    path = profile(tmp_path, monkeypatch, "11111111-1111-4111-8111-111111111111")
    path.chmod(mode)
    with pytest.raises(ConfigurationError, match="not group/other writable"):
        GatewaySettings.from_environment()


@requires_posix_root
@pytest.mark.parametrize("kind", ["symlink", "directory", "non_root_owner"])
def test_runtime_profile_rejects_untrusted_file_identity(tmp_path, monkeypatch, kind):
    path = profile(tmp_path, monkeypatch, "11111111-1111-4111-8111-111111111111")
    if kind == "symlink":
        target = path.with_name("real-runtime.json")
        path.rename(target)
        path.symlink_to(target)
    elif kind == "directory":
        path.unlink()
        path.mkdir(mode=0o700)
    else:
        os.chown(path, 65534, 65534)
    with pytest.raises(ConfigurationError):
        GatewaySettings.from_environment()


@requires_posix_root
@pytest.mark.parametrize("mode", [0o600, 0o640, 0o644])
def test_runtime_metadata_compatibility_does_not_relax_oss_credentials(tmp_path, mode):
    path = tmp_path / "oss.env"
    path.write_text("OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com\n"
                    "OSS_BUCKET=shared-bucket\nOSS_ACCESS_KEY_ID=fixture\n"
                    "OSS_ACCESS_KEY_SECRET=fixture\n", encoding="utf-8")
    path.chmod(mode)
    if mode == 0o600:
        assert load_oss_credentials(path).bucket == "shared-bucket"
    else:
        with pytest.raises(ConfigurationError, match="0600 or stricter"):
            load_oss_credentials(path)


@pytest.mark.parametrize('change',[{'organizationId':'../../another'},{'environment':'../production'},{'objectStorage':{'namespaceMode':'enterprise-v1','rootPrefix':'enterprises/another/staging/apps'}}])
def test_shared_scope_rejects_untrusted_identity_or_override(tmp_path,monkeypatch,change):
    path=profile(tmp_path,monkeypatch,'11111111-1111-4111-8111-111111111111')
    body=json.loads(path.read_text());body.update(change);path.write_text(json.dumps(body))
    with pytest.raises(ConfigurationError):GatewaySettings.from_environment()


def test_two_enterprises_same_slug_same_bucket_remain_isolated(tmp_path,monkeypatch):
    storage=FakeStorageAdapter();clients=[]
    for index in [1,2]:
        root=tmp_path/str(index);root.mkdir(mode=0o700)
        organization=str(UUID(int=index))
        profile(root,monkeypatch,organization)
        settings=replace(GatewaySettings.from_environment(),db_path=root/'registry.db',apps_env_dir=root/'env',spool_dir=root/'spool',minimum_free_bytes=1)
        registry=CredentialRegistry(settings.db_path)
        app=registry.ensure_app('orders',settings.apps_env_dir,settings.internal_url)
        client=TestClient(create_app(registry=registry,storage=storage,settings=settings))
        clients.append((client,_auth(_read_token(app.env_path))))
    for index,(client,headers) in enumerate(clients):
        assert client.put('/v1/objects/report.txt',headers=headers,content=f'company-{index}'.encode()).status_code==201
    for index,(client,headers) in enumerate(clients):
        assert client.get('/v1/objects/report.txt',headers=headers).content==f'company-{index}'.encode()
        assert client.get('/v1/objects/enterprises/other/staging/apps/orders/report.txt',headers=headers).status_code==404
    assert len(storage.objects)==2
    assert all(k.startswith('enterprises/') for k in storage.objects)


def test_shared_prefix_probe_checks_other_enterprise_and_backup_namespace(monkeypatch):
    import sys
    from types import SimpleNamespace
    seen=[]
    class Forbidden(Exception):status=403
    class Bucket:
        def call(self,key):seen.append(key);raise Forbidden()
        def list_objects_v2(self,*,prefix,max_keys):return self.call(prefix)
        def head_object(self,key):return self.call(key)
        def delete_object(self,key):return self.call(key)
        def put_object(self,key,*args,**kwargs):return self.call(key)
    monkeypatch.setitem(sys.modules,'oss2',SimpleNamespace(Auth=lambda *_:None,Bucket=lambda *_:Bucket()))
    current='11111111-1111-4111-8111-111111111111'
    _assert_outside_prefix_denied(OssCredentials('https://oss-cn-hangzhou.aliyuncs.com','shared-bucket','test','test'),'run',f'enterprises/{current}/staging/apps')
    assert len(seen)==12
    assert any('/backups/' in p for p in seen)
    assert any(p.startswith('enterprises/') and current not in p for p in seen)
