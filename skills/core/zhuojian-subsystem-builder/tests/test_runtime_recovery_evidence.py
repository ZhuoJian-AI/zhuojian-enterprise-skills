import importlib.util
import json
from pathlib import Path
import sys

SCRIPTS=Path(__file__).parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
import runtime_backup_oss as transport
import runtime_recovery_evidence as evidence


def fixture(tmp_path):
    profile={'organizationId':'65130a23-b05e-4026-9615-761ab2d4193c','runtimeId':'aifabei-hk-01','enterpriseKey':'aifabei','environment':'staging','deployment':{'backupsRoot':str(tmp_path)}}
    plan={**{k:profile[k] for k in ['organizationId','runtimeId','environment']},'source_id':'alphabet-runtime-aifabei-hk-01','host_id':'runtime:aifabei-hk-01','applications':{'example':{'name':'Example','primary_sqlite':'/data/subsystem.db'}}}
    archive=tmp_path/'example/20261027T120000Z-aaaaaaaaaaaa.tar.gz';archive.parent.mkdir();archive.write_bytes(b'never read by observer')
    components={name:{'included':True,'verified':True,'count':0,'bytes':0} for name in ['database','local_files','oss_files','code','config']}
    meta={'schemaVersion':3,'applicationSlug':'example','archive':archive.name,'createdAt':'2026-10-27T12:01:00Z','capturedAt':'2026-10-27T12:00:00Z','commit':'a'*40,'sha256':'b'*64,'sizeBytes':123,'components':components,'limitations':[]}
    transport.atomic_json(archive.with_suffix('.gz.json'),meta)
    return profile,plan,archive


def test_observation_keeps_original_point_times_and_does_not_read_archive(tmp_path,monkeypatch):
    profile,plan,archive=fixture(tmp_path)
    read_bytes=Path.read_bytes
    def guarded(path,*args,**kwargs):
        assert path.suffix!='.gz','observer read a business archive body'
        return read_bytes(path,*args,**kwargs)
    monkeypatch.setattr(Path,'read_bytes',guarded)
    value=evidence.observe(profile,plan,now='2026-10-27T13:00:00Z')
    system=value['systems'][0];point=system['latest_successful_point']
    assert system['observed_at']=='2026-10-27T13:00:00Z'
    assert point['captured_at']=='2026-10-27T12:00:00Z' and point['completed_at']=='2026-10-27T12:01:00Z'
    assert point['components']['oss_files']['included'] is True and point['components']['oss_files']['count']==0
    assert point['offsite']['status']=='not_configured'


def test_failed_latest_job_retains_successful_point_and_hides_private_locators(tmp_path):
    profile,plan,archive=fixture(tmp_path)
    transport.atomic_json(archive.parent/'online-job.json',{'status':'failed','attempt_at':'2026-10-27T12:30:00Z','finished_at':'2026-10-27T12:31:00Z','error_code':'offsite_failed','archive':'another-new-point','private_uri':'oss://sensitive/location','secret':'never expose'})
    value=evidence.observe(profile,plan,now='2026-10-27T13:00:00Z')
    system=value['systems'][0]
    assert system['latest_job']['status']=='failed' and system['latest_successful_point']['point_id']==archive.name
    text=json.dumps(value)
    assert 'sensitive' not in text and 'secret' not in text and str(tmp_path) not in text and 'oss://' not in text


def test_component_projection_drops_unknown_private_metadata(tmp_path):
    profile,plan,archive=fixture(tmp_path)
    path=archive.with_suffix('.gz.json');meta=transport.read_json(path)
    meta['components']['database']['private_uri']='oss://never/expose'
    meta['limitations']=['runtime_services_not_started','oss://never/expose']
    transport.atomic_json(path,meta)
    assert 'oss://' not in json.dumps(evidence.observe(profile,plan))


def test_partial_restore_requires_same_point_and_keeps_service_limit(tmp_path):
    profile,plan,archive=fixture(tmp_path)
    receipt={'archiveName':archive.name,'sha256':'b'*64,'verifiedAt':'2026-10-27T12:10:00Z','businessDatabaseVerified':True,'gitVerified':True,'fileHashesVerified':True,'referenceIntegrityVerified':True}
    transport.atomic_json(archive.with_suffix('.gz.restore.json'),receipt)
    restore=evidence.observe(profile,plan)['systems'][0]['latest_successful_point']['restore']
    assert restore['result']=='partial' and 'runtime_services_not_started' in restore['limitations']
    receipt['sha256']='c'*64;transport.atomic_json(archive.with_suffix('.gz.restore.json'),receipt)
    assert evidence.observe(profile,plan)['systems'][0]['latest_successful_point']['restore']['result']=='not_tested'


def test_registered_project_mapping_is_taken_from_plan(tmp_path):
    profile,plan,archive=fixture(tmp_path)
    plan['applications']['example']['project_id']='registered-project:unrelated-to-slug'
    system=evidence.observe(profile,plan)['systems'][0]
    assert system['project_id']=='registered-project:unrelated-to-slug'
    assert system['latest_successful_point']['project_ids']==['registered-project:unrelated-to-slug']


def test_new_local_failed_upload_does_not_hide_older_verified_offsite_point(tmp_path):
    profile,plan,new=fixture(tmp_path)
    old=new.with_name('20261027T110000Z-aaaaaaaaaaaa.tar.gz');old.write_bytes(b'older')
    meta=transport.read_json(new.with_suffix('.gz.json'));meta.update(archive=old.name,createdAt='2026-10-27T11:01:00Z',capturedAt='2026-10-27T11:00:00Z')
    transport.atomic_json(old.with_suffix('.gz.json'),meta)
    remote={'archive':old.name,'sha256':meta['sha256'],'applicationSlug':'example','offServer':True,'organizationId':profile['organizationId'],
            'runtimeId':profile['runtimeId'],'environment':profile['environment'],'uploadedAt':'2026-10-27T11:02:00Z','fullReadbackAt':'2026-10-27T11:03:00Z','versionId':'exact-older-version'}
    transport.atomic_json(old.with_suffix('.gz.remote.json'),remote)
    transport.atomic_json(new.parent/'online-job.json',{'status':'failed','attempt_at':'2026-10-27T12:00:00Z','finished_at':'2026-10-27T12:02:00Z','error_code':'offsite_failed','archive':new.name})
    system=evidence.observe(profile,plan)['systems'][0]
    assert system['latest_job']['status']=='failed'
    assert system['latest_successful_point']['point_id']==old.name
    assert system['latest_successful_point']['offsite']['status']=='verified'


def test_uploaded_new_point_with_failed_restore_preserves_older_recovery_proof(tmp_path):
    profile,plan,new=fixture(tmp_path)
    old=new.with_name('20261027T110000Z-aaaaaaaaaaaa.tar.gz');old.write_bytes(b'older')
    meta=transport.read_json(new.with_suffix('.gz.json'));meta['archive']=old.name
    transport.atomic_json(old.with_suffix('.gz.json'),meta)
    for archive in (old,new):
        remote={'archive':archive.name,'sha256':meta['sha256'],'applicationSlug':'example','offServer':True,'organizationId':profile['organizationId'],
                'runtimeId':profile['runtimeId'],'environment':profile['environment'],'uploadedAt':'2026-10-27T11:02:00Z','fullReadbackAt':'2026-10-27T11:03:00Z','versionId':'exact-version'}
        transport.atomic_json(archive.with_suffix('.gz.remote.json'),remote)
    transport.atomic_json(old.with_suffix('.gz.restore.json'),{'archiveName':old.name,'sha256':meta['sha256'],'verifiedAt':'2026-10-27T11:04:00Z',
        'businessDatabaseVerified':True,'gitVerified':True,'fileHashesVerified':True,'referenceIntegrityVerified':True})
    transport.atomic_json(new.parent/'online-job.json',{'status':'failed','attempt_at':'2026-10-27T12:00:00Z','finished_at':'2026-10-27T12:02:00Z','error_code':'restore_failed','archive':new.name})
    system=evidence.observe(profile,plan)['systems'][0]
    assert system['latest_job']['error_code']=='restore_failed' and system['latest_successful_point']['point_id']==old.name
