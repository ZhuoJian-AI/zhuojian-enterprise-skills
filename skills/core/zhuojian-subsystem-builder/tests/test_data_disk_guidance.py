from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_data_disk_guidance_is_routed_from_admin_entrypoints() -> None:
    skill = read("SKILL.md")
    bootstrap = read("references/admin-bootstrap.md")

    assert "references/data-disk-capacity.md" in skill
    assert "data-disk-capacity.md" in bootstrap


def test_data_disk_guidance_keeps_destructive_actions_bounded() -> None:
    guidance = read("references/data-disk-capacity.md")

    assert "明确授权初始化" in guidance
    assert "使用 UUID 写入 `/etc/fstab`" in guidance
    assert "不得重新格式化" in guidance
    assert "禁止全局 `docker system prune`" in guidance
    assert "数据库或整个 Docker 数据根只允许在独立停机迁移计划中处理" in guidance


def test_block_disk_is_not_reported_as_object_storage() -> None:
    object_storage = read("references/object-storage.md")

    assert "挂载云盘仍属于 `local-managed`" in object_storage
    assert "不得把“文件位于独立云盘”报告成“已迁移 OSS”" in object_storage
