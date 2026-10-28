import datetime as dt
import json
from pathlib import Path
import socket

import pytest

from zhuojian_storage_gateway.config import OssCredentials, load_oss_credentials
from zhuojian_storage_gateway.storage import BusinessLeaseProvider, StorageUnavailable, create_oss_auth


def expiration(seconds):
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=seconds)).isoformat()


def write_lease(path, *, key='test-key-one', expires=None):
    path.write_text('OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com\nOSS_BUCKET=business-bucket\n'
        'OSS_ACCESS_KEY_ID=' + key + '\nOSS_ACCESS_KEY_SECRET=test-secret\nOSS_SECURITY_TOKEN=test-token\n'
        'OSS_CREDENTIAL_PROVIDER=platform-sts-v1\nOSS_EXPIRES_AT=' + (expires or expiration(900)) + '\n')
    path.chmod(0o600)


def test_sdk_provider_rereads_atomic_lease_for_each_request(tmp_path):
    import oss2
    path = tmp_path / 'lease.env'
    write_lease(path)
    auth = create_oss_auth(load_oss_credentials(path), oss2)
    assert isinstance(auth, oss2.ProviderAuth)
    assert auth.credentials_provider.get_credentials().get_access_key_id() == 'test-key-one'
    replacement = tmp_path / 'replacement'
    write_lease(replacement, key='test-key-two')
    replacement.replace(path)
    assert auth.credentials_provider.get_credentials().get_access_key_id() == 'test-key-two'


def test_gateway_renewal_requests_only_fixed_business_socket(tmp_path, monkeypatch):
    path = tmp_path / 'lease.env'
    write_lease(path, expires=expiration(60))
    seen = []
    payload = {'ok': True, 'credentials': {'OSS_ENDPOINT': 'https://oss-cn-hangzhou.aliyuncs.com',
        'OSS_BUCKET': 'business-bucket', 'OSS_ACCESS_KEY_ID': 'new-test-key', 'OSS_ACCESS_KEY_SECRET': 'new-test-secret',
        'OSS_SECURITY_TOKEN': 'new-test-sts', 'OSS_EXPIRES_AT': expiration(900)}}
    class Client:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def settimeout(self, value):
            pass
        def connect(self, value):
            seen.append(value)
        def sendall(self, value):
            seen.append(value)
        def recv(self, _limit):
            return json.dumps(payload).encode() + b'\n'
    monkeypatch.setattr(socket, 'AF_UNIX', 1, raising=False)
    monkeypatch.setattr(socket, 'socket', lambda *_args: Client())
    provider = BusinessLeaseProvider(load_oss_credentials(path))
    assert provider.get_credentials().get_access_key_id() == 'new-test-key'
    assert seen == ['/run/zhuojian-oss-lease/business/credentials.sock', b'GET\n']
    assert 'runtime-registration' not in repr(seen) and 'backup' not in repr(seen)


def test_expired_lease_cannot_fall_back_to_static_or_another_bucket(tmp_path, monkeypatch):
    path = tmp_path / 'lease.env'
    write_lease(path, expires=expiration(-1))
    monkeypatch.setattr(socket, 'AF_UNIX', 1, raising=False)
    def unavailable(*_args):
        raise OSError('test unavailable')
    monkeypatch.setattr(socket, 'socket', unavailable)
    with pytest.raises(StorageUnavailable, match='renewal is unavailable'):
        BusinessLeaseProvider(load_oss_credentials(path)).get_credentials()
    write_lease(path)
    provider = BusinessLeaseProvider(load_oss_credentials(path))
    path.write_text(path.read_text().replace('business-bucket', 'backup-bucket'))
    with pytest.raises(StorageUnavailable, match='scope changed'):
        provider.get_credentials()


def test_static_gateway_credentials_keep_original_auth():
    import oss2
    static = OssCredentials('https://oss-cn-hangzhou.aliyuncs.com', 'business-bucket', 'test', 'test')
    assert isinstance(create_oss_auth(static, oss2), oss2.Auth)
    compose = (Path(__file__).parents[1] / 'compose.yaml').read_text()
    assert '/etc/zhuojian/oss-business-lease:/run/secrets/zhuojian-oss-business:ro' in compose
    assert 'runtime-registration.key' not in compose and 'backup-oss.env' not in compose
