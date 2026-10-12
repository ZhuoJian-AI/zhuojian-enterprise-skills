# 通用企业插件的子系统开发契约

2026-10-12。用户授权实施通用企业插件、保留浏览器助手并更新 Builder Skill。本项从 `origin/main` 的 `1997f35e5af3bddde47ed5d117775555496e6485` 建立独立工作树及 `codex/enterprise-client-action-contract-20261012` 分支；源仓库主工作树及其他分支未改。core `1.1.31` 是本地候选，尚未推送、合并或发布稳定 Release。

后续用户明确要求推送并部署，本轮已推送候选并创建非草稿 [PR #66](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/pull/66)。发布路线沿用原 bundle 构建器，候选为 core `1.1.31` / `bundle-v1.4.32`；须 PR 与合并源码 CI、干净主分支构建、其他四个 Skill ZIP 不变及匿名公开安装验证分别通过后补正式回执。此段只记录发布准备，不宣称合并或 Release 已完成；正文中未推送等描述保留为最初检查点。

## 责任与范围

- Skill 主责：补充 `references/external-agent-access.md`，在入口、平台契约、业务交付和文件存储说明中按调用宿主区分责任，保留 `2.4/2.5`、Manifest Schema、Runtime 模板及更新器。
- SaaS 主责：企业 OAuth、通用 remote MCP、服务端绑定企业/员工、当前获权目录、Schema 摘要、业务确认/幂等、撤权与文件提交。此仓库没有实现或部署这些接口。
- 外部宿主使用自身推理及本机代码环境，浏览器助手保留。员工插件不携带 Builder 开发 Skill、SSH/root、Runtime 秘密或服务器访问档案。
- 子系统复用现有业务服务；若登记、权限、Schema、结果与幂等已符合要求，可只复用登记。缺口需逐系统核对，本次未修改或部署任何现有企业子系统。
- 本次不改企业专属 Skills、平台代码、生产、连接账号或已有 OAuth 授权。未创建 PR、推送、发布、更新组织 Wiki 或执行 managed Skill 批量更新。

## 契约重点

稳定发现/详情/调用入口每次读取最新获权目录，旧 Schema 摘要不得套用新语义；Schema 与业务记录版本分开。Wiki 仅提供业务背景；客户端工具允许不代表业务确认。确认与逻辑操作幂等绑定具体主体、目标、参数及版本，未知结果先核对。宿主本机产物必须受控提交并取得实际工作空间文件版本回执，才能宣称平台交付；上传未知不重复先前成功业务写入。动态 MCP 工具通知与客户端刷新能力分别验收，不承诺所有客户端热刷新。

## 验证

- 在 core Skill 目录执行 `python -m pytest -q`：**522 passed, 53 skipped, 1 warning in 28.61s**。53 项套件跳过不计通过；一条警告来自现有 Starlette/AnyIO 依赖弃用。
- 实际解释器为 `D:/Agent_Project/SaaS-platform/audit-2026-09-27/dual-device-release-tests/venv/Scripts/python.exe`。系统 `python` 是不可用的 WindowsApps 别名，首次命令退出 1 且无输出，未计验证通过；未安装依赖或修改全局 PATH。
- `quick_validate.py skills/core/zhuojian-subsystem-builder`：`Skill is valid!`。
- 修改文档的 **64 个本地相对文件链接**存在，`git diff --check` 通过。现有版本测试同步为 1.1.31，默认/兼容接入版本仍是 2.5 / 2.4、2.5。
- 本项是规范变更；没有把文本匹配测试当运行时行为证明。OAuth、跨租户、实际宿主刷新、真实业务写入、文件提交及电脑/手机流程需在对应运行实现中另外验收。

## 双账号精确同步

同步前，两个账号各 7 个待改既有文件均与 Git 基线内容一致，新参考两边都不存在，无版本冲突。对两边先完成原文件备份及 SHA-256 校验，再逐项写入并复核；仅同步本次 **8 个 Builder 文件**：

```text
SKILL.md
references/external-agent-access.md
references/platform-contract.md
references/business-ai-delivery.md
references/object-storage.md
skill-version.json
CHANGELOG.md
tests/test_contract_versions.py
```

目标为 `C:/Users/codex02/.codex/skills/zhuojian-subsystem-builder` 与 `C:/Users/王鑫涛/.codex/skills/zhuojian-subsystem-builder`。每边 **8/8 SHA-256 与本次候选源码匹配**；其余文件分别核对 codex02 **158** 项、王鑫涛 **149** 项，文件集合和内容均未变。不同已有文件数量被保留，不按目录差异清理。

本机脱敏回执和备份位于 `D:/Agent_Project/zhuojian-enterprise-skills-client-contract-evidence-20261012/`：`sync-receipt.json` 逐文件记录原/新哈希和备份路径，`backups/<account>/` 保存原始 7 文件，`sync-builder.ps1` 保留本次精确同步步骤。仅本机按授权应用候选差异，不代表稳定发布；其他设备仍走现有不可变 Release 通道。
