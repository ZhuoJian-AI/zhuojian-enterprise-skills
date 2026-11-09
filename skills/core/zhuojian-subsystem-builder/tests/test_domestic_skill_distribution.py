"""Stable Skill content rides the existing domestic distribution pointer."""
import pytest
import update_skill
import update_managed_skills

BASE = "https://ai-platform.staging.zhuojianai.com/enterprise-plugin/updates/"
URL = BASE + "downloads/0.1.39/zhuojian-subsystem-builder-1.1.54.zip"

def update():
    return dict(schemaVersion=1, skillName=update_skill.SKILL_NAME, channel="stable",
                skillVersion="1.1.54", archiveUrl=URL, archiveSha256="a"*64)

def test_native_pointer_selects_core_without_using_plugin_version():
    wrapper = dict(schemaVersion=1, version="0.1.39", skillUpdates={update_skill.SKILL_NAME:update()})
    assert update_skill.validate_update_manifest(wrapper,allow_test_url=False) == ("1.1.54",URL,"a"*64)

@pytest.mark.parametrize("bad", [
    "https://evil.example/enterprise-plugin/updates/downloads/core.zip",
    "http://ai-platform.staging.zhuojianai.com/enterprise-plugin/updates/downloads/core.zip",
    URL+"?token=bad", URL+"#fragment",
    URL.replace("https://","https://user:password@"),
])
def test_archive_origin_and_no_credentials_boundary(bad):
    with pytest.raises(update_skill.UpdateError):
        update_skill.validate_download_url(bad,allow_test_url=False)
    with pytest.raises(update_managed_skills.ManagedUpdateError):
        update_managed_skills.validate_download_url(bad,allow_test_url=False)

def test_pointer_still_validates_inner_identity():
    wrong=update();wrong["skillName"]="another-skill"
    with pytest.raises(update_skill.UpdateError):
        update_skill.validate_update_manifest({"skillUpdates":{update_skill.SKILL_NAME:wrong}},allow_test_url=False)

def test_catalog_uses_its_own_stable_repository_contract():
    catalog=dict(schemaVersion=1,channel="stable",repository=update_managed_skills.REPOSITORY,
                 skills={"zhuojian-subsystem-builder":dict(update(),kind="core",enterpriseKeys=[],runtimeIds=[],hosts=[])})
    releases=update_managed_skills.validate_catalog({"version":"0.1.39","skillCatalog":catalog},allow_test_url=False)
    assert releases["zhuojian-subsystem-builder"].version=="1.1.54"
    catalog["repository"]="attacker/skills"
    with pytest.raises(update_managed_skills.ManagedUpdateError):
        update_managed_skills.validate_catalog({"skillCatalog":catalog},allow_test_url=False)

