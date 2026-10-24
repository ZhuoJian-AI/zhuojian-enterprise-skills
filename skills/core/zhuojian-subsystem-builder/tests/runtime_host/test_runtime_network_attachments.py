"""Root approvals and native deploy/start/rollback network ordering, no Docker needed."""
import argparse
import contextlib
import copy
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('network_attachment_runtime_tests', ROOT / 'assets/admin-runtime/host/runtime_admin.py')
h = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = h
SPEC.loader.exec_module(h)


class NetworkAttachmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paths = h.Paths(runtime=self.root / 'runtime.json', state=self.root / 'state.json')
        self.paths.state.write_text('{}')
        self.profile = dict(runtimeId='target-runtime', organizationId='10000000-0000-4000-8000-000000000001',
                            environment='staging', enterpriseKey='example')
        self.item = {'name': 'example-readonly-route', 'id': 'a' * 64}
        self.record = dict(schema=1, contract=h.NETWORK_ATTACHMENTS_CONTRACT, application_slug='orders',
                           runtime_alias='target-runtime', organization_id=self.profile['organizationId'],
                           environment='staging', enterprise_key='example', networks=[self.item])
        self.network = dict(Id=self.item['id'], Name=self.item['name'], Driver='bridge', Scope='local',
                            Internal=True, Ingress=False, ConfigOnly=False, ConfigFrom={'Network': ''},
                            IPAM={'Driver': 'default', 'Config': [{'Subnet': '172.29.94.0/24', 'Gateway': '172.29.94.1', 'IPRange': ''}]})
        self.release = dict(applicationSlug='orders', containerName='zhuojian-example-orders',
                            envFile=str(self.root / 'orders.env'), dataDir=str(self.root / 'data'),
                            port=18007, hostname='orders.example.com', storageMode='local-managed')
        self.image = 'zhuojian/example/orders:' + 'b' * 40

    def write_record(self, record=None):
        directory = self.root / 'network-attachments'
        directory.mkdir(exist_ok=True, mode=0o700)
        path = directory / 'orders.json'
        path.write_text(json.dumps(self.record if record is None else record))
        path.chmod(0o600)
        return path

    def result(self, value=None, code=0):
        return subprocess.CompletedProcess([], code, json.dumps(value) if value is not None else '', '')

    def test_no_record_performs_no_docker_discovery(self):
        with mock.patch.object(h, 'run') as run:
            self.assertEqual(h.validated_network_attachments('orders', self.profile, self.paths), [])
        run.assert_not_called()

    def test_exact_internal_network_and_native_empty_iprange_are_accepted(self):
        self.write_record()
        with mock.patch.object(h, 'assert_network_attachment_path'), mock.patch.object(h, 'run', return_value=self.result([self.network])) as run:
            self.assertEqual(h.validated_network_attachments('orders', self.profile, self.paths), [self.item])
        self.assertEqual(run.call_args.args[0], ['docker', 'network', 'inspect', self.item['id']])

    def test_wrong_owner_slug_schema_unknown_fields_and_duplicate_ids_fail_before_docker(self):
        variants = [dict(self.record, **{key: value}) for key, value in (
            ('organization_id', 'wrong'), ('runtime_alias', 'other'), ('environment', 'production'),
            ('enterprise_key', 'other'), ('application_slug', 'other'), ('schema', True), ('extra', 'from-metadata'),
            ('networks', [self.item, self.item]))]
        for record in variants:
            with self.subTest(record=record):
                self.write_record(record)
                with mock.patch.object(h, 'assert_network_attachment_path'), mock.patch.object(h, 'run') as run:
                    with self.assertRaises(h.AdminError):
                        h.validated_network_attachments('orders', self.profile, self.paths)
                run.assert_not_called()

    def test_duplicate_json_fields_fail(self):
        path = self.write_record()
        path.write_text(path.read_text().replace('"schema": 1', '"schema": 1, "schema": 1'))
        with mock.patch.object(h, 'assert_network_attachment_path'), self.assertRaises(h.AdminError):
            h.validated_network_attachments('orders', self.profile, self.paths)

    def test_replaced_external_overlay_or_unknown_ipam_network_is_refused(self):
        self.write_record()
        variants = [dict(self.network, **{key: value}) for key, value in (
            ('Id', 'c' * 64), ('Name', 'renamed'), ('Internal', False), ('Driver', 'overlay'),
            ('Scope', 'swarm'), ('Ingress', True), ('ConfigOnly', True))]
        bad_ipam = copy.deepcopy(self.network)
        bad_ipam['IPAM']['Config'][0]['IPRange'] = '172.29.94.0/25'
        variants.append(bad_ipam)
        for network in variants:
            with self.subTest(network=network):
                with mock.patch.object(h, 'assert_network_attachment_path'), mock.patch.object(h, 'run', return_value=self.result([network])):
                    with self.assertRaises(h.AdminError):
                        h.validated_network_attachments('orders', self.profile, self.paths)
        with mock.patch.object(h, 'assert_network_attachment_path'), mock.patch.object(h, 'run', return_value=self.result(code=1)), self.assertRaises(h.AdminError):
            h.validated_network_attachments('orders', self.profile, self.paths)

    def test_unsafe_root_record_metadata_is_rejected(self):
        for field, value in (('uid', 1000), ('record_mode', 0o640), ('directory_mode', 0o750), ('record_mode', stat.S_IFLNK | 0o777), ('size', 20000)):
            with self.subTest(field=field):
                values = dict(uid=0, record_mode=stat.S_IFREG | 0o600, directory_mode=stat.S_IFDIR | 0o700, size=100)
                values[field] = value
                path = mock.Mock(parents=[])
                path.lstat.return_value = mock.Mock(st_mode=values['record_mode'], st_uid=values['uid'])
                path.stat.return_value = mock.Mock(st_mode=values['record_mode'], st_size=values['size'])
                path.parent.stat.return_value = mock.Mock(st_mode=values['directory_mode'])
                path.is_file.return_value = True
                with mock.patch.object(h.os, 'name', 'posix'), mock.patch.object(h.os, 'geteuid', return_value=0, create=True), self.assertRaises(h.AdminError):
                    h.assert_network_attachment_path(path)
        with mock.patch.object(h.os, 'name', 'posix'), mock.patch.object(h.os, 'geteuid', return_value=1000, create=True), self.assertRaises(h.AdminError):
            h.assert_network_attachment_path(mock.Mock())

    def start(self, attachments, fail_connect=False):
        calls = []
        started = False
        def run(argv, **kwargs):
            nonlocal started
            calls.append(argv)
            if argv[:3] == ['docker', 'network', 'connect'] and fail_connect:
                raise h.AdminError('synthetic connect failure')
            if argv[:2] == ['docker', 'start']:
                started = True
            if argv[:2] == ['docker', 'inspect']:
                networks = {'bridge': {'NetworkID': 'd' * 64}}
                networks.update({item['name']: {'NetworkID': item['id'] if started else ''} for item in attachments})
                return self.result([{'State': {'Running': started}, 'Config': {'Image': self.image}, 'NetworkSettings': {'Networks': networks}}])
            return self.result()
        with mock.patch.object(h, 'validated_network_attachments', return_value=attachments), mock.patch.object(h, 'container_exists', return_value=False), mock.patch.object(h, 'verify_upload_lock'), mock.patch.object(h, 'run', side_effect=run):
            if fail_connect:
                with self.assertRaises(h.AdminError):
                    h.start_container(self.release['containerName'], self.image, self.release, 'orders', self.profile, self.paths)
            else:
                h.start_container(self.release['containerName'], self.image, self.release, 'orders', self.profile, self.paths)
        return calls

    def test_absent_record_keeps_original_run_flags_and_primary_network(self):
        calls = self.start([])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][:3], ['docker', 'run', '--detach'])
        self.assertNotIn('--network', calls[0])
        self.assertEqual(calls[0][-1], self.image)

    def test_approved_route_is_connected_by_id_before_first_start(self):
        calls = self.start([self.item])
        self.assertEqual([row[:2] for row in calls], [['docker', 'create'], ['docker', 'network'], ['docker', 'inspect'], ['docker', 'start'], ['docker', 'inspect']])
        self.assertEqual(calls[1], ['docker', 'network', 'connect', self.item['id'], self.release['containerName']])
        self.assertNotIn('--detach', calls[0])
        self.assertNotIn('--network', calls[0])
        self.assertEqual(calls[0][-1], self.image)

    def test_connect_failure_never_starts_or_deletes_created_container_or_data(self):
        calls = self.start([self.item], fail_connect=True)
        self.assertEqual([row[:2] for row in calls], [['docker', 'create'], ['docker', 'network']])
        self.assertFalse(any(row[:2] in (['docker', 'start'], ['docker', 'rm']) for row in calls))

    def test_deploy_and_rollback_refuse_invalid_network_before_recovery_or_stop(self):
        for operation in (h.cmd_deploy, h.cmd_rollback):
            with self.subTest(operation=operation.__name__):
                with mock.patch.object(h, 'locked', return_value=contextlib.nullcontext()), mock.patch.object(h, 'load_runtime', return_value=self.profile), mock.patch.object(h, 'validated_network_attachments', side_effect=h.AdminError('changed ID')), mock.patch.object(h, 'recover_pending_release_switch') as recover, mock.patch.object(h, 'run') as run:
                    with self.assertRaises(h.AdminError):
                        operation(argparse.Namespace(application_slug='orders'), self.paths)
                recover.assert_not_called()
                run.assert_not_called()

    def test_native_rollback_uses_the_same_create_connect_start_path(self):
        release = dict(self.release, current={'commit': 'c' * 40, 'image': 'zhuojian/example/orders:' + 'c' * 40},
                       history=[{'commit': 'b' * 40, 'image': self.image}], nginxConfig=str(self.root / 'orders.conf'))
        marker = {'rollbackContainer': 'previous-orders', 'previousCommit': 'c' * 40,
                  'previousImage': release['current']['image']}
        calls = []
        started = False
        def run(argv, **kwargs):
            nonlocal started
            calls.append(argv)
            if argv[:2] == ['docker', 'start']:
                started = True
            if argv[:2] == ['docker', 'inspect']:
                return self.result([{'State': {'Running': started}, 'Config': {'Image': self.image},
                                     'NetworkSettings': {'Networks': {'bridge': {}, self.item['name']: {'NetworkID': self.item['id'] if started else ''}}}}])
            return self.result()
        with contextlib.ExitStack() as stack:
            patches = {'locked': mock.Mock(return_value=contextlib.nullcontext()), 'load_runtime': mock.Mock(return_value=self.profile),
                       'load_release': mock.Mock(return_value=release), 'recover_pending_release_switch': mock.Mock(return_value=release),
                       'validated_network_attachments': mock.Mock(return_value=[self.item]), 'run': mock.Mock(side_effect=run),
                       'inspect_managed_release_container': mock.Mock(return_value={'running': True}),
                       'assert_container_release_identity': mock.Mock(), 'wait_for_health': mock.Mock(),
                       'create_release_switch_marker': mock.Mock(return_value=marker), 'persist_release_switch_phase': mock.Mock(),
                       'begin_platform_release_change': mock.Mock(return_value=True), 'read_optional_plain': mock.Mock(return_value=b'old'),
                       'replace_nginx': mock.Mock(), 'nginx_text': mock.Mock(return_value='server {}'), 'atomic_json': mock.Mock(),
                       'container_exists': mock.Mock(return_value=False), 'verify_upload_lock': mock.Mock()}
            for name, value in patches.items():
                stack.enter_context(mock.patch.object(h, name, value))
            result = h.cmd_rollback(argparse.Namespace(application_slug='orders', commit=None, health_timeout=20), self.paths)
        self.assertEqual(result['commit'], 'b' * 40)
        operations = [row[:2] for row in calls]
        self.assertIn(['docker', 'stop'], operations)
        self.assertNotIn(['docker', 'run'], operations)
        create_index = operations.index(['docker', 'create'])
        connect_index = operations.index(['docker', 'network'])
        start_index = operations.index(['docker', 'start'])
        self.assertLess(create_index, connect_index)
        self.assertLess(connect_index, start_index)
        self.assertEqual(calls[connect_index][3], self.item['id'])


if __name__ == '__main__':
    unittest.main()
