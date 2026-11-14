"""Actual HTTP checks for the optional server client; never a real account."""
import importlib.util
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import pytest

spec=importlib.util.spec_from_file_location('application_user_client',Path(__file__).resolve().parents[1]/'assets/application_user_client.py')
client_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(client_module)
Client,Error=client_module.ApplicationUserClient,client_module.ApplicationUserError


@pytest.fixture
def broker():
    state={'calls':[],'status':200,'app':'owned-app'}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            state['calls'].append((self.path,self.headers['Authorization'],body))
            self.send_response(state['status']);self.send_header('Content-Type','application/json')
            if state['status']==302:self.send_header('Location','http://127.0.0.1:1/foreign')
            self.end_headers()
            self.wfile.write(json.dumps({'id':'membership','application_id':state['app'],
                'external_id':body.get('external_id'),'subject_id':'platform-person'}).encode())
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    state['origin']='http://127.0.0.1:'+str(server.server_port)
    try:yield state
    finally:server.shutdown();server.server_close();thread.join()


def test_registration_preserves_source_and_optional_proof(broker):
    client=Client(broker['origin'],'zjss_isolated-fixture',application_id='owned-app',allow_http_loopback=True)
    result=client.register(external_id='local-stable-01',source_version=8,business_roles=['original-role'],identity_link_token='proof-fixture')
    assert result['subject_id']=='platform-person'
    path,credential,body=broker['calls'][0]
    assert path=='/api/v1/subsystem-users/register' and credential=='Bearer zjss_isolated-fixture'
    assert body['external_id']=='local-stable-01' and body['source_version']==8
    assert body['business_roles']==['original-role'] and body['identity_link_token']=='proof-fixture'
    assert 'zjss_isolated-fixture' not in repr(client)
    assert not any('password' in key for key in body)


def test_checks_never_relogin_and_redirects_do_not_forward_credentials(broker):
    client=Client(broker['origin'],'zjss_isolated-fixture',application_id='owned-app',allow_http_loopback=True)
    broker['status']=401
    with pytest.raises(Error) as rejected:client.check('session-fixture')
    assert rejected.value.status==401 and len(broker['calls'])==1
    broker['status']=302
    with pytest.raises(Error) as redirect:client.login('local-id')
    assert redirect.value.status==302 and len(broker['calls'])==2
    assert 'session-fixture' not in str(rejected.value)


def test_wrong_app_response_and_insecure_origins_rejected(broker):
    client=Client(broker['origin'],'zjss_isolated-fixture',application_id='owned-app',allow_http_loopback=True)
    broker['app']='other-app'
    with pytest.raises(Error) as wrong:client.register(external_id='original',source_version=1)
    assert wrong.value.status==502
    for origin in ['http://public.example','https://user:secret@example.test','https://example.test/other','https://example.test?secret=1']:
        with pytest.raises(ValueError):Client(origin,'zjss_isolated-fixture',application_id='owned-app')
    with pytest.raises(ValueError):Client(broker['origin'],'zjss_isolated-fixture',application_id='owned-app')
