---
name: aifabei-subsystem-builder
description: "历史兼容入口：把仍在调用 aifabei-subsystem-builder 的用户自动迁移到 zhuojian-subsystem-builder。旧用户提到 Alphabet 模块、企业 ECS 或灼见接入时使用；新任务直接使用 zhuojian-subsystem-builder。"
---

# 旧名称兼容入口

`aifabei-subsystem-builder` 不再是跨企业总入口。正式总 Skill 是 `zhuojian-subsystem-builder`，总仓库仍是 `ZhuoJian-AI/zhuojian-enterprise-skills`。

每次调用本 Skill 时：

1. 运行 `python <skill>/scripts/update_skill.py`。若输出 `SKILL_UPDATED`，立即读取新版本记录并重新读取本文件。
2. 运行 `python <skill>/scripts/update_managed_skills.py install-core zhuojian-subsystem-builder`。
3. 若输出 `MANAGED_SKILLS_CURRENT` 或 `MANAGED_SKILLS_UPDATED`，立即读取同级 `zhuojian-subsystem-builder/skill-version.json`、对应更新记录和 `SKILL.md`，随后完全按新 Skill 继续当前任务。
4. 若新总 Skill 尚未安装且迁移失败，停止依赖企业环境的操作，只报告“总 Skill 暂时无法更新，请保持网络可访问 GitHub 后重试”。不要删除旧副本，也不要根据历史名称猜测公司或服务器规则。

业务负责人不需要重新领取 Skill、不需要 GitHub 账号，也不需要再次提供已经建立长期访问记忆的服务器密码。
