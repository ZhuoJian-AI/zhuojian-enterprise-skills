"""Runtime/SDK integration fixtures for exact SaaS-attested legacy origins."""
import argparse
import contextlib
import copy
import importlib.util
import json
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value
fixture=load('origin_host_fixture',Path(__file__).with_name('test_runtime_admin.py'))
runtime=fixture.runtime_admin
publisher=load('origin_publisher_fixture',ROOT/'scripts/publish_subsystem.py')

class RegisteredOriginAdoptionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.paths=fixture.RuntimeHostTests().paths(Path(self.temp.name));self.profile=fixture.RuntimeHostTests().profile(self.paths)
        self.profile.update(runtimeId='target-runtime',environment='staging',platform={'baseUrl':'https://platform.example.com'})
        self.paths.runtime.write_text(json.dumps(self.profile),encoding='utf-8')
        self.args=argparse.Namespace(application_slug='orders',application_id='10000000-0000-4000-8000-000000000001',source_runtime_id='20000000-0000-4000-8000-000000000002',base_url='https://orders.old-runtime.example.com',commit='a'*40)
        self.target='30000000-0000-4000-8000-000000000003'
        self.module=dict(application_slug='orders',application_id=self.args.application_id,organization_id=self.profile['organizationId'],runtime_id=self.args.source_runtime_id,requester_runtime_id=self.target,owned_by_requester=False,base_url=self.args.base_url,status='healthy',last_success_commit=self.args.commit)
        self.cap=dict(protocol='zhuojian-platform-capabilities',features={'registeredApplicationOriginRegistration':dict(runtime.ORIGIN_REGISTRATION_CAPABILITY)})
        self.addCleanup(mock.patch.stopall)
        mock.patch.dict(os.environ,{'ZHUOJIAN_ADMIN_TESTING':'1'}).start()
        mock.patch.object(runtime.os,'geteuid',return_value=0,create=True).start()
        # The test account may be non-root; actual metadata enforcement remains
        # unconditional in production and is separate from these protocol cases.
        mock.patch.object(runtime,'assert_origin_adoption_path').start()
        mock.patch.object(publisher,'assert_registered_origin_path').start()
    def adopt(self,module=None,cap=None):
        with mock.patch.object(runtime,'platform_release_request',side_effect=[(200,cap or self.cap),(200,module or self.module)]) as request:
            value=runtime.cmd_adopt_origin(self.args,self.paths)
        return value,request
    def record(self):return runtime.load_origin_adoption('orders',self.profile,self.paths)
    def test_exact_healthy_source_adopts_without_changing_runtime_profile(self):
        original=self.paths.runtime.read_bytes();result,request=self.adopt();record=self.record()
        self.assertEqual(result['applicationId'],self.args.application_id);self.assertFalse(result['servicesChanged']);self.assertEqual(original,self.paths.runtime.read_bytes())
        self.assertEqual(runtime.expected_names('orders',self.profile,self.paths)['hostname'],'orders.old-runtime.example.com')
        self.assertEqual(publisher.load_registered_origin(self.paths.runtime,self.profile,'orders',self.args.base_url),record)
        self.assertEqual([call.args[2] for call in request.call_args_list],['GET','GET'])
        self.assertTrue(all(call.kwargs['no_redirect'] for call in request.call_args_list))
    def test_missing_capability_and_wrong_attested_identity_are_refused(self):
        variants=[('organization_id','40000000-0000-4000-8000-000000000004'),('application_id','40000000-0000-4000-8000-000000000004'),('base_url','https://new-origin.example.com'),('runtime_id',self.target),('last_success_commit','b'*40),('owned_by_requester',True),('requester_runtime_id',None)]
        for field,value in variants:
            with self.subTest(field=field):
                module=dict(self.module,**{field:value})
                with self.assertRaises(runtime.AdminError):self.adopt(module=module)
                self.assertFalse(runtime.origin_adoption_path('orders',self.paths).exists())
        with self.assertRaises(runtime.AdminError):self.adopt(cap={'protocol':'zhuojian-platform-capabilities','features':{}})
    def test_source_replay_never_begins_another_runtime_change(self):
        self.adopt()
        with mock.patch.object(runtime,'platform_release_request',side_effect=[(200,self.cap),(200,self.module)]) as request:
            self.assertFalse(runtime.begin_platform_release_change(self.profile,self.paths,'orders','a'*40))
        self.assertEqual([call.args[2] for call in request.call_args_list],['GET','GET'])
        with mock.patch.object(runtime,'platform_release_request',side_effect=[(200,self.cap),(200,self.module)]),self.assertRaises(runtime.AdminError):
            runtime.begin_platform_release_change(self.profile,self.paths,'orders','b'*40)
    def test_sdk_requires_capability_exact_first_commit_and_owned_target_later(self):
        self.adopt();record=self.record()
        with mock.patch.object(publisher,'call_json',side_effect=[self.cap,self.module]):
            self.assertEqual(publisher.require_registered_origin(self.profile,'not-a-real-token',record,'a'*40),'source')
        with mock.patch.object(publisher,'call_json',side_effect=[self.cap,self.module]),self.assertRaises(SystemExit):
            publisher.require_registered_origin(self.profile,'not-a-real-token',record,'b'*40)
        owned=dict(self.module,runtime_id=self.target,owned_by_requester=True,status='failed')
        with mock.patch.object(publisher,'call_json',side_effect=[self.cap,owned]):
            self.assertEqual(publisher.require_registered_origin(self.profile,'not-a-real-token',record,'b'*40),'target')
        with mock.patch.object(publisher,'call_json',return_value={'features':{}}),self.assertRaises(SystemExit):
            publisher.require_registered_origin(self.profile,'not-a-real-token',record,'a'*40)
    def test_tampered_record_and_new_origin_fail_both_readers(self):
        self.adopt();record=self.record()
        with self.assertRaises(SystemExit):publisher.load_registered_origin(self.paths.runtime,self.profile,'orders','https://new-origin.example.com')
        record['base_url']='https://new-origin.example.com';record['record_sha256']=runtime.origin_adoption_digest({k:v for k,v in record.items() if k!='record_sha256'})
        runtime.origin_adoption_path('orders',self.paths).write_text(json.dumps(record))
        with self.assertRaises(runtime.AdminError):self.record()
        with self.assertRaises(SystemExit):publisher.load_registered_origin(self.paths.runtime,self.profile,'orders',record['base_url'])
    def test_seven_ordinary_apps_and_adopted_app_share_backup_without_profile_replacement(self):
        self.adopt();slugs=['ordinary-'+str(i) for i in range(7)]+['orders']
        for slug in slugs:
            names=runtime.expected_names(slug,self.profile,self.paths)
            if slug!='orders':self.assertEqual(names['hostname'],slug+'.aifabei.example.com')
            path=runtime.release_path(slug,self.paths);path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(dict(names,managedBy=runtime.MANAGED_BY,port=18000+slugs.index(slug),current={'commit':'a'*40,'image':'example:test'})))
        with mock.patch.object(runtime,'recover_pending_release_switch',side_effect=lambda release,*args:release),mock.patch.object(runtime,'backup_one',side_effect=lambda slug,*args:{'applicationSlug':slug}):
            result=runtime.cmd_backup_all(argparse.Namespace(),self.paths)
        self.assertTrue(result['ok']);self.assertEqual(len(result['backups']),8)
    def test_real_sdk_main_registers_original_app_at_attested_origin_and_rejects_changed_result(self):
        self.adopt();project=Path(self.temp.name)/'project';project.mkdir()
        key=Path(self.temp.name)/'dummy-runtime-key';key.write_text('not-a-real-token')
        release=dict(managedBy=runtime.MANAGED_BY,applicationSlug='orders',containerName='zhuojian-aifabei-orders',status='awaiting_platform_registration',current={'commit':'a'*40,'image':'zhuojian/aifabei/orders:'+'a'*40})
        environment={k:prefix+'x'*40 for k,prefix in [('ZHUOJIAN_MANIFEST_ACCESS_TOKEN','zjmf_'),('ZHUOJIAN_SSO_EXCHANGE_TOKEN','zjss_'),('ZHUOJIAN_ACTION_SIGNING_SECRET','zjac_'),('ZHUOJIAN_EVENT_SIGNING_SECRET','zjev_')]}
        manifest=dict(applicationSlug='orders',applicationName='Orders',enterprise={'key':'aifabei'},contractRevision='2.5')
        argv=['publish_subsystem.py','--project-path',str(project),'--base-url',self.args.base_url,'--application-slug','orders','--runtime-profile',str(self.paths.runtime),'--runtime-credential-file',str(key)]
        for wrong_result in (False,True):
            result=dict(self.module,runtime_id=self.target,owned_by_requester=True)
            if wrong_result:result['application_id']='90000000-0000-4000-8000-000000000009'
            def request(url,token,method='GET',body=None,**kwargs):
                if url.endswith('/platform-capabilities'):return self.cap
                if url.endswith('/modules/orders'):return self.module
                if url.endswith('/api/integration/manifest'):return manifest
                if url.endswith('/modules/register'):return result
                raise AssertionError('Unexpected request')
            with self.subTest(wrong_result=wrong_result),mock.patch.object(publisher.sys,'argv',argv),mock.patch.object(publisher,'runtime_locked',return_value=contextlib.nullcontext()),mock.patch.object(publisher,'git',side_effect=lambda project,*args:'' if args[0]=='status' else 'a'*40),mock.patch.object(publisher,'load_app_environment',return_value=environment),mock.patch.object(publisher,'load_runtime_release',return_value=release),mock.patch.object(publisher,'verify_running_container'),mock.patch.object(publisher,'require_publishable_navigation_theme'),mock.patch.object(publisher,'require_publishable_checkbox_permissions'),mock.patch.object(publisher,'reload_verified_runtime_release',return_value=release),mock.patch.object(publisher,'update_runtime_release_status') as update,mock.patch.object(publisher,'call_json',side_effect=request) as network,contextlib.redirect_stdout(io.StringIO()):
                if wrong_result:
                    with self.assertRaises(SystemExit):publisher.main()
                    update.assert_not_called()
                else:
                    self.assertEqual(publisher.main(),0);update.assert_called_once()
                    posted=next(call for call in network.call_args_list if call.args[0].endswith('/modules/register'))
                    self.assertEqual(posted.args[3]['base_url'],self.args.base_url)
                    self.assertFalse(any('/begin-change' in call.args[0] for call in network.call_args_list))

if __name__=='__main__':unittest.main()
