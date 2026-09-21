# NAS 只读规范稳定版发布证据

2026-09-21，用户确认实施 Skill 合并、稳定发布及本机更新。

- 审查 PR #31 的完整差异：规则仅作用于明确要求原件留在 NAS 的外部只读资料源；普通附件存储、接入协议与 Runtime 不变。无新增阻断问题。此为本次执行者复核，不声称独立人工批准。
- PR #31 已合并，source `b7df0d29f2bfd50ad3729ef1f0dbfb753e205cfb`。
- 合并树与已验证 ec3d1df 完全相同（git diff --exit-code）；沿用 244 passed、41 skipped 和两个 Skill quick_validate 的结果。
- 干净合并工作树运行 `python scripts/build_release.py --tag bundle-v1.4.17 --output-dir <独立资产目录>` 成功，5 个 ZIP 的 SHA-256 与 catalog 全部一致。
- 稳定版 https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.17 已公开发布为 latest，包含 9 个必需资产。
- 全新空目录、公开无凭据 updater 安装：SKILL_UPDATED installed 1.1.17。
- 同一空目录 resolve aifabei / aifabei-hk-01 / 8.218.208.205：匹配 NAS handoff 1.0.1 和既有道讯 handoff 1.1.0，正确安装。
- 本机总 Skill：SKILL_UPDATED 1.1.16 -> 1.1.17。
- 本机 NAS handoff：MANAGED_SKILLS_UPDATED 1.0.0 -> 1.0.1；其他已有 handoff 保持 current。

本次仅发布 Skill；未修改或部署 SaaS、Runtime、NAS 子系统或其他三个业务子系统。共享盘实际验收未完成项继续以其交接记录为准，不能用本次 Skill 发布消除这些待办。

规则依据：zhuojian-server-deploy 43dff14（2026-09-20）。
