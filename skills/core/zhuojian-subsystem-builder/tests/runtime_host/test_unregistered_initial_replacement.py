"""Initial-candidate repair never clears a registered release or skips its CAS."""
import argparse,copy,importlib.util,sys,unittest
from pathlib import Path
from unittest import mock

fixture_path=Path(__file__).with_name('test_runtime_admin.py')
spec=importlib.util.spec_from_file_location('initial_repair_host_fixture',fixture_path)
fixture=importlib.util.module_from_spec(spec);sys.modules[spec.name]=fixture;spec.loader.exec_module(fixture)
runtime=fixture.runtime_admin

class UnregisteredInitialReplacementTests(unittest.TestCase):
    def setUp(self):
        self.sha='a'*40
        self.args=argparse.Namespace(replace_unregistered_initial=True,expected_current_commit=self.sha)
        self.release={'applicationSlug':'orders','status':'awaiting_platform_registration','history':[], 'current':{'commit':self.sha,'image':'zhuojian/example/orders:'+self.sha}}
        self.profile={'enterpriseKey':'example'}
    def verify(self,status=404):
        with mock.patch.object(runtime,'validated_recorded_release_identity',return_value=(self.sha,'image')) as identity, mock.patch.object(runtime,'platform_release_request',return_value=(status,{})) as request:
            result=runtime.verify_unregistered_initial_replacement(self.args,self.release,self.profile,runtime.PATHS)
        return result,identity,request
    def test_live_absence_and_exact_pin_are_required_without_mutating_state(self):
        before=copy.deepcopy(self.release);result,identity,request=self.verify()
        self.assertEqual(self.release,before);self.assertEqual(result['commit'],self.sha);self.assertTrue(result['platformModuleAbsent'])
        self.assertEqual(request.call_args.args[2:4],('GET','/api/v1/ecs-publisher/modules/orders'))
        self.assertTrue(request.call_args.kwargs['allow_not_found']);identity.assert_called_once()
    def test_existing_platform_record_is_not_replaceable(self):
        for status in [200,201,401,403,409,500]:
            with self.subTest(status=status),self.assertRaises(runtime.AdminError):self.verify(status)
    def test_missing_explicit_flag_pin_or_empty_history_refuses_before_network(self):
        variants=[('flag',False),('pin','b'*40),('history',[{'commit':'c'*40}]),('status','healthy')]
        for name,value in variants:
            with self.subTest(name=name):
                self.setUp()
                if name=='flag':self.args.replace_unregistered_initial=value
                elif name=='pin':self.args.expected_current_commit=value
                else:self.release[name]=value
                with mock.patch.object(runtime,'validated_recorded_release_identity',return_value=(self.sha,'image')),mock.patch.object(runtime,'platform_release_request') as request,self.assertRaises(runtime.AdminError):
                    runtime.verify_unregistered_initial_replacement(self.args,self.release,self.profile,runtime.PATHS)
                request.assert_not_called()
    def test_network_failure_does_not_mutate_candidate(self):
        before=copy.deepcopy(self.release)
        with mock.patch.object(runtime,'validated_recorded_release_identity',return_value=(self.sha,'image')),mock.patch.object(runtime,'platform_release_request',side_effect=runtime.AdminError('offline')),self.assertRaises(runtime.AdminError):
            runtime.verify_unregistered_initial_replacement(self.args,self.release,self.profile,runtime.PATHS)
        self.assertEqual(self.release,before)

if __name__=='__main__':unittest.main()
