# 连续自适应纠错规范

任务 `CONTINUOUS-RESPONSIVE-CONTRACT-20260927`，Codex；基线 `a9a545b`，部署规则 `43dff14`。用户要求记录此次宽屏失误，避免反复针对单一电脑/手机尺寸修补。

## 原因与调整

SaaS 员工首页背景误套正文限宽，既有固定视口验收未覆盖宽屏和浏览器缩放后的实际可用空间。本仓负责后续开发规范，当前运行时代码由 `ai-platform` 修复；规范本身不能修复已上线页面。

补充核心 Skill 入口、`references/platform-contract.md` 及生成项目 `AGENTS.md`：电脑/手机分别设计交互，各自内部连续自适应；背景铺满与正文限宽分离，内容可收缩/换行，卡片容纳可见内容。在固定矩阵之外持续缩放同一会话，覆盖窄窗口、超宽屏、断点两侧、侧栏变化、长内容、低高度及失败状态；检查内部裁切、操作可达与业务状态保持，区分模拟与真机。

没有新增协议字段、改变 2.4/2.5、修改业务模板运行代码或升级版本号。规则适用于后续相关页面开发；不会自动重做或部署已接入的生产协同、商品动销、企业文化或公司共享盘。下游无立即迁移截止日期。

## 验证与状态

- `python C:/Users/王鑫涛/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/core/zhuojian-subsystem-builder`：通过。
- `python -m pytest skills/core/zhuojian-subsystem-builder/tests/test_generated_native_template.py skills/core/zhuojian-subsystem-builder/tests/test_native_template_responsive.py -q`：4 passed，12.93s。
- 本次为文档修正，未新增匹配文案的测试；既有生成与浏览器模板检查不代表所有业务页面已自适应。
- 当前是本地源规范候选，未推送、未合并、未发布稳定 Skill 包。本机已安装稳定包仍为 1.1.23；当前助手另通过全局 `AGENTS.md` 的长期要求执行此规范。
- 发布范围：后续经授权合并并发布 `zhuojian-enterprise-skills` 稳定包；无需部署 SaaS 服务或企业 ECS。本次 SaaS 修复、服务构建及浏览器验证在对应 `ai-platform` 交接单列。

## 稳定发布准备（2026-09-27）

用户明确要求“推送部署吧”，授权发布本轮候选。执行者 Codex responsive-skill-release；规则依据本轮刷新的 `43dff14`。本仓仅发布 Skill，SaaS 实现与 staging 发布由主任务负责；不连接或部署企业业务 ECS。

稳定版本递增为 core 1.1.24 / bundle-v1.4.24，并同步既有版本断言和 CHANGELOG。完整测试、独立审查、PR/main CI、干净合并构建、公开新装及本机升级将在完成后逐项记录。生成模板中的 AGENTS 为下游可复制规范，发布后按跨仓库流程通知已核实使用方；既有系统无立即迁移或强制重部署要求，也无截止日期。

- 在已有隔离 Python 3.10 环境从本工作树核心目录运行 `python -m pytest -q -ra`：458 passed、41 skipped、1 warning，23.73 秒；其中 38 个模板占位集成测试由生成项目子套件执行，3 个 POSIX 权限语义检查在 Windows 未覆盖。依赖的弃用提示不影响退出码 0。
- 核心 Skill `quick_validate.py` 与 `git diff --check` 通过。本轮未修改 Schema、Runtime、模板运行代码或更新器，测试结果不代表真实业务页面或手机真机均已验收。
