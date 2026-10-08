# 撤回超出本轮范围的 Builder 修改

用户于2026-10-08明确纠正：本轮需要修改的是“灼见服务器部署”Skill，不包括 `zhuojian-subsystem-builder`。因此撤回本轮误纳入的 Builder PR #64，不将已有源码合并视为继续发行的依据。

## 精确范围

- 在新工作树、分支 `codex/revert-builder-gateway-scope-20261008`，从当时最新 `origin/main` / `e8ecda8a98ced09f41ace6b29fc1fcd63c403df8` 开始。
- 执行 `git revert --no-commit -m 1 e8ecda8a98ced09f41ace6b29fc1fcd63c403df8`，只反向应用该合并相对第一父提交的改动；不重置分支、不改写历史、不覆盖其他人的工作。
- Builder 的规则、参考、随包“模块需求”、生成AGENTS、版本元数据、CHANGELOG和测试断言均恢复；与第一父提交 `539d060c0bd787deb6239597a68e81ddc7e2e24a` 的整个 `skills/core/zhuojian-subsystem-builder` 目录差异为空。版本恢复1.1.30，契约2.4/2.5保持。
- 误改的候选任务/交接记录撤回，新增本文件记录原因与真实状态。没有修改其他四个 Skill、部署 Skill、SaaS、网关或服务器。

## 发行与安装边界

误改的源 PR #64 曾通过PR/main CI并合并；其 bundle-v1.4.32 九个资产仅在隔离审计目录完成构建及校验，用户叫停后保留为本地未发行记录。没有创建该tag/Release，没有上传资产，公开匿名安装验收脚本未运行。

本回退不发行新的稳定包，不修改两账号真实安装。匿名读取公开latest稳定manifest得到HTTP200，仍为bundle-v1.4.31/core1.1.30，压缩包SHA256为 `6cc903ffe852ff2468cb014b186da3d3eccb078ab0e57fd81069b5a6628fd32a`；远端 `bundle-v1.4.32` 标签检查为空。两账号只读版本均为1.1.30，逐一核对156个公开包文件全部匹配、无缺失或不同；codex02另有4个既存 `scripts/__pycache__/*.pyc`，王鑫涛无额外文件，均未清理或修改。不能将包文件匹配误报为两边均零额外文件。现有业务子系统无需因这次误改或回退自动重建、同步或部署。

## 验证与状态

在恢复后的核心目录使用现有CPython3.10.21环境执行完整 `python -m pytest -q`（缓存与临时目录位于隔离审计目录）：**522 passed / 53 skipped / 1 warning，23.21秒，退出0**。跳过为既有Windows/POSIX及原始模板检查边界，警告为既有AnyIO别名弃用。Builder `quick_validate.py` 通过；`git diff --check`、暂存差异检查及整个Builder目录相对539d060的零差异核对通过。未新增或修改执行代码、模板或协议。

本机原始日志及只读安装证据保存在 `audit-2026-10-08/builder-gateway-scope-revert/`，包括 `core-full.log`、`public-stable-manifest.json`、`installation-readonly-verification.json`。回退PR/CI/合并由协调结果另行报告；本文件记录提交前已完成的验证，不提前宣称远端已合并。

回退仅纠正本轮范围，不改变独立模型网关运行时的实际实现或部署结果。
