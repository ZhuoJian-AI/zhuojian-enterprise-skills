# SaaS 三入口契约的本地补充

本轮主责为 Skill 接入契约，依据 SaaS `docs/development/browser-surfaces.md` 与三端发布交接。源码基线为 `ZhuoJian-AI/zhuojian-enterprise-skills` main `9b5d03dd3fcb6f7b5ffe2be5dfe2cc36a8030da5`；已安装版本为 core `1.1.31`。本地只补正文，不分配新稳定版本、不构建 Release；源码未推送/合并，不能将本次文件称为新的公开稳定包。

## 范围

- `SKILL.md` 增加按需入口；`references/platform-contract.md` 区分 console/admin/workplace 与业务来源；`references/external-agent-access.md` 保留 MCP/OAuth 与原同源管理员身份桥。
- 子系统 SSO、Bridge、权限、文件来源及 `contractRevision=2.4/2.5` 保持；模板、Runtime、验证器、插件包和业务子系统未改、未部署。
- 具体域名和生产上线以目标环境真实登记/验收为准，不写计划域名为已上线事实。

## 本地验证和同步

- `python -m pytest -q tests/test_ai_delivery.py tests/test_runtime_auto_release_contract.py tests/test_contract_versions.py`：39 passed。
- `skill-creator/scripts/quick_validate.py`：通过；Markdown 相对链接、YAML 与 `git diff --check` 另作静态核对。
- 指定的上述三份正文及本交接同步至 `codex02`、`王鑫涛` 两账号同名 Skill，保留无关文件；先备份旧字节，再核对两份结果。同步回执和备份保存在本机 SaaS 审查目录 `audit-2026-10-12/skill-surface-sync/`。
- 本轮为文档契约补充，不重跑生产业务、真机或 Runtime 测试，也不以 Skill 同步证明 SaaS 三端上线。后续公开发布需单独分配版本、更新 changelog 并按既有稳定 Release 流程验收。
