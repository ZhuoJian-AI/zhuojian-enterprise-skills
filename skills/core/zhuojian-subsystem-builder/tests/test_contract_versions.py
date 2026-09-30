from __future__ import annotations

import json
from pathlib import Path

import pytest

from contract_versions import (
    detect_project_contract_revision,
    load_skill_metadata,
    require_supported_contract_revision,
)


ROOT = Path(__file__).resolve().parents[1]


def test_skill_release_version_is_separate_from_contract_revision() -> None:
    metadata = load_skill_metadata(ROOT)

    assert metadata["skillVersion"] == "1.1.26"
    assert metadata["defaultContractRevision"] == "2.5"
    assert metadata["supportedContractRevisions"] == ["2.4", "2.5"]


def test_module_theme_coordinates_assistant_chrome_without_styling_content() -> None:
    guidance = (ROOT / "references" / "module-navigation-migration.md").read_text(encoding="utf-8")

    assert "**同一统一助手**入口／外框／顶部／输入控件" in guidance
    assert "平台骨架、结构、名称和普通文字必须保持中性" in guidance
    assert "助手内容、审批与错误等语义状态" in guidance
    assert "缺失或无效的既有登记回退平台默认色" in guidance
    assert "离开应用时必须清除主题" in guidance


def test_detect_project_revision_is_read_only(tmp_path: Path) -> None:
    manifest_path = tmp_path / "subsystem.json"
    manifest_path.write_text(json.dumps({
        "protocol": "zhuojian-subsystem",
        "version": 2,
        "contractRevision": "2.4",
    }), encoding="utf-8")
    before = manifest_path.read_bytes()

    assert detect_project_contract_revision(tmp_path) == "2.4"
    assert manifest_path.read_bytes() == before


def test_optional_name_is_not_an_authorization_or_form_requirement() -> None:
    guidance = (ROOT / "references" / "action-permission-scopes.md").read_text(encoding="utf-8")
    assert "显示姓名是可选展示元数据，不是授权凭据" in guidance
    assert "不能以姓名为空禁用提交，或把只读姓名输入设为必填" in guidance
    assert "不能按同名认领历史记录" in guidance
    assert "有前置条件的事务内修复" in guidance
    assert "不为验收替真实员工打卡" in guidance


def test_unknown_contract_revision_is_not_guessed() -> None:
    with pytest.raises(ValueError, match="不支持的 contractRevision"):
        require_supported_contract_revision("2.6")
