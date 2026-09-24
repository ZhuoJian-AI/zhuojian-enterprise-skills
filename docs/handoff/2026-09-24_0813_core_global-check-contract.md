# 登录期跨页面只读检查：Skill 契约交接

- 执行者：Codex（独立工作树 `codex/global-check-skill-20260924`）
- 任务：`ASSISTANT-GLOBAL-CHECK-20260924`
- 规则依据：本仓 `AGENTS.md` 与 core Skill `AGENTS.md`；灼见规则 SHA `43dff14`。从 `origin/main` 的 `c566e62` 起步。本条原为候选记录；实际发布状态以文末“稳定发布完成”一节为准。

## 本次改变

- 在既有 2.4/2.5 Manifest 的页面 `aiSemantics` 增加可选 `globalCheck`：`actionKey` 必填，`intervalSeconds` 60..3600，缺省 300。同一应用的同一 Action 不得被多个页面重复登记。
- 绑定 Action 必须是本页获权只读 `query`，`aiEnabled=true`、`requiresConfirmation=false`，不得含 `platformAiCapability`；参数固定 `{"context":{}}`，输入 Schema 必须是仅有必填空封闭 context 的封闭对象。它不借用当前页面对象或浏览器数据，也不给其他普通查询放宽 `limit`。结果沿用封闭的 `result.assistantCheck` v1，至多三条建议及 16 KiB；稳定 `id/revision/dataVersion` 来自业务证据，不从轮询时间生成。
- core 入口、流程参考、业务提效参考与平台契约说明了两种不同语义：`proactiveCheck` 仍是员工开启且当前页可见；`globalCheck` 只供登录 SaaS 外壳跨页面低频读取。SaaS 按员工的应用/模块/登记页面/Action 权限发现和调用，子系统再按签名身份与业务记录范围过滤；模型供应商、唯一助手、会话和确认仍由 SaaS 控制。
- `assistantCheck` v1 没有独立的 source/asOf 字段，因此数据来源、最近可核实的业务时点与限制只可写在 `summary`/建议摘要并由真实业务验收；Schema 通过**不能证明新鲜度**。历史、手工或静态数据不能称实时预警；失败、无权或来源不可核实不能冒充“无风险”。首版不承诺离线通知、后台扫描、事件启动 LangGraph、自动发送或无人值守写入。
- 模板不默认生成虚构 `globalCheck`；只有真实业务处理器、权限和数据口径可验证时才由下游明确登记。现有 `assistantWorkflowGuidance` 当前页能力声明不能单独证明 SaaS 全局消费已经部署。

## 核对与未完成

- `python -m pytest -q tests/test_global_check.py tests/test_workflow_guidance.py`：97 passed；最终 `python -m pytest -q`：456 passed、41 skipped。覆盖 2.4/2.5 兼容、间隔边界、固定参数、真实 Action 引用、结果 Schema、普通查询 `limit`、重复登记及现有 `proactiveCheck`；源码 CLI 也使用同一校验。
- `python C:/Users/王鑫涛/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/core/zhuojian-subsystem-builder`：`Skill is valid!`。`git diff --check`：通过。
- 运行命令与最终结果见本提交验证记录；这些是 Skill 包内测试，不是 SaaS、Runtime 或生产协同的跨服务器验收。
- 待 SaaS 实际实现并验证登录期发现、权限隔离、错误反馈、去重与桌面/手机展示；待具体子系统实现真实只读 Action 和业务测试。生产协同旧进度底表含静态资料，在未核实实时来源前只能提示“待核对”，不能向员工宣称实时进度风险。其他未适配子系统保持原功能。
- 发布边界：本分支已推送并建立 PR #41，现为待评审状态；尚未合并、构建稳定 Release 或部署 SaaS/Runtime/ECS。Skill 文档与校验器修改不代表服务器同步。发布时仍须按仓库评审、稳定包与下游通知流程执行。

## 2026-09-24 发布准备补充

- 按稳定更新规则将 core Skill 升至候选 `1.1.22`，添加同版本更新记录和版本测试；`contractRevision` 继续保持 2.4／2.5，不做协议迁移。
- 重新运行 core 全量测试：456 passed、41 skipped；`quick_validate.py` 通过，`git diff --check` 通过。PR #41 由草稿转待评审；远端 Core Skill CI 运行 `35943527943` 已通过。评审、合并与稳定 Release 尚未完成。
- 用本分支校验器检查生产协同候选 `subsystem.json`：0 项错误；同一 Manifest 经 SaaS 候选校验器接受，子系统只读 Action 的模拟业务快照结果也经 SaaS `AssistantCheck` 模型接受。这是跨仓**本地契约验证**，不是真实员工授权、企业服务器 Action 或在线提醒验收。
- 用户明确选择“暂不授权”试点角色；本轮不增加员工 Action 或数据范围，获权账号的线上提醒效果须待以后显式授权再验收。

## 2026-09-24 发布审查修正

- SaaS 源码 PR #380 已合并为 `b4ba7214670bacf17d0bf9e54349f7e2c8e4e3a3`，镜像清单 PR #381 已合并为 `84116d05c39657246d807fbd6ff6fa68f2537e6d`；受保护发布 `maintenanced253a5d720634ecbdfe2` 完成，九个服务健康，公开 `/health` 正常。这只证明 SaaS 发布与技术健康，不证明员工已收到提醒。
- 独立评审指出 `globalCheck` 绑定 Action 可遗漏 `permissionPolicy`，与新增 Action 必须声明权限策略的契约不符。候选校验器已限定仅在声明 `globalCheck` 时强制要求，并增加缺失策略及旧 Manifest 兼容测试；未给旧 2.4/2.5 Action 全局加新门禁。
- 用户选择“暂不授权”，所以只可验证无权拒绝、Manifest 登记及健康路径；获权员工的跨页面提醒、范围隔离和撤权回归待以后授权后完成。本次不得报告主动业务预警已完成验收。生产协同 ECS 与 Skill 稳定 Release 的实际发布状态以各自发布记录为准，不从 SaaS 已发布推断完成。
- 生产协同 ECS `8.218.208.205` 已从 `86c2630d85e2951281126dd39dc45ac3f85ddd40` 切换到 `e3cae7a98fc65914a959cfc799664276081fe06e`；候选镜像隔离环境 91 项测试通过，旧版备份已留存。Runtime `verify-release` 和 `status` 均返回 healthy，平台同应用 Manifest 登记返回 healthy、`authorization: unchanged; new capabilities require administrator approval`。这同样不等于员工获权路径已验收；另三个子系统没有部署。

## 2026-09-24 稳定发布完成

- PR #41 经独立审查、缺失 `permissionPolicy` 问题修正后合并为 `ff7a60ed141114696bdb568c3548e8fad93d0971`。core 1.1.22 全量测试 458 passed、41 skipped；`quick_validate.py` 和主分支 CI 通过。从干净的合并后 `main` 构建并公开发布 `bundle-v1.4.22`，九个 Release 资产的远端 SHA-256 均与本地一致；core ZIP SHA-256 为 `3d11785ac8a7c9cf68365bc39986f0e50c37433f785f764271f2b860367b438f`。
- 官方更新器的公开全新安装、重复更新 CURRENT 和本机 1.1.21→1.1.22 安装通过。Skill 稳定发布是开发接入契约已可用，不自动修改已有子系统或用户权限。
- 本次跨层同步范围：SaaS 已独立受控发布；生产协同在企业 ECS 独立部署并登记；其他三个子系统未改代码、未部署。用户明确选择“暂不授权”试点角色；真实获权员工的跨页面提醒出现、撤回和范围隔离仍待授权后验收，不能称为全员主动预警已验证。
