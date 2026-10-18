# 通用消息委托与本人草稿例外

基线：公共仓库 `origin/main f4d8440`，独占分支 `codex/message-delegation-20261018`。准备 core 1.1.35，保留契约 2.4/2.5。本记录为本地修改与测试，尚无 PR、push、稳定 Release 或服务器部署。

## 责任与改动

- SaaS：目录、逐 Action 当前员工授权、完整可信确认、钉钉投递和回执；另行源码提交与发布，本 Skill 不代替运行时。
- 子系统：通知业务页面、本人草稿、业务记录及发送 Action，沿用企业管理员原有角色授权入口。
- Skill：`message-delivery.md` 描述通用接口及边界；可选 Manifest `messageDelivery` 校验要求 create/employeeDirectory/本人确认，不新增企业分支、角色名或服务器配置。
- `validate_ai_delivery.py` 仅为证据明确的本人私有、本地无外部副作用 create/update 草稿接受 `bindings[].privateDraft`。发送、删除、审批及其他未声明写入保持原确认规则；本地证据声明不授权运行。
- 不修改 Runtime、原生模板、更新器、其他企业 Skills 或现有子系统。旧 Runtime 不投影新能力时如实待验，目标 SaaS 必须独立上线并验证。

## 验证

- WSL 独立副本 `/tmp/zj-message-skill-tests-20261018-fjajeyyr`：`pytest -q tests/test_ai_delivery.py tests/test_permission_policy.py tests/test_manifest_schema_versions.py`，111 passed、101 subtests passed。
- `quick_validate.py`：WSL 及 Windows 均 `Skill is valid!`；`git diff --check` 通过。
- 首次借用后端 WSL 环境全量测试：545 passed、55 skipped、7 failed。其中 1 项版本断言已随版本更新，6 项来自旧 Runtime 的 root 文件权限及模板运行环境；未放宽生产检查。root 重跑时生成模板子进程等待，停止仅本次拥有的测试进程。
- 按仓库 Windows CI 依赖新建隔离 venv，保留 FastAPI 0.116.1、httpx 0.28.1、jsonschema 4.25.1、Playwright 1.60.0。执行 core `python -B -m pytest -q --tb=short`：553 passed、53 skipped、1 failed。唯一失败为未改动原生模板的 Windows 临时 SQLite 文件占用（业务用例 71 passed、1 skipped，teardown 出错）；仅复跑该 `test_scaffolded_native_system_runs_its_security_and_recovery_suite`：1 passed，9.56 秒。不把跳过项或模拟浏览器当真机验收。
- 安装测试依赖生成的 gateway `build/`、`src/zhuojian_storage_gateway.egg-info/` 不提交、不复制到 Skill；清理请求被自动审批策略拒绝，保留本地可丢弃产物，未绕过。

## 双账号精确同步

两个安装目录均为 1.1.34。同步前逐文件比较当前安装、Git 基线与新文件，12 个变更路径均无无关冲突；仅同步这些路径，两账号 24 次 SHA-256 校验一致。其他文件不动。

- `C:/Users/codex02/.codex/skills/zhuojian-subsystem-builder`
- `C:/Users/王鑫涛/.codex/skills/zhuojian-subsystem-builder`

原文件备份和前后哈希：本机审计目录 `audit-2026-10-18/enterprise-notifications/skill-sync-backup-1.1.35/sync-manifest.json`。本文件随后作为已授权随附交接同步；稳定 Release 尚未发布，不能据此称其他开发者已自动升级。

## 待发布与验收

由主任务完成 review/PR、版本冻结与稳定 Release，按总仓规则从干净合并提交构建并验证公开匿名安装。目标 SaaS、独立通知子系统、网页/助手/钉钉完整确认和真实投递分别验收；本 Skill 没有向真实员工发送消息、增加角色权限或修改生产数据。
