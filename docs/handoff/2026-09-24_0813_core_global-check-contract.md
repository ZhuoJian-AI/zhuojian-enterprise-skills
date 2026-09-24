# 登录期跨页面只读检查：Skill 契约交接

- 执行者：Codex（独立工作树 `codex/global-check-skill-20260924`）
- 任务：`ASSISTANT-GLOBAL-CHECK-20260924`
- 规则依据：本仓 `AGENTS.md` 与 core Skill `AGENTS.md`；灼见规则 SHA `43dff14`。从 `origin/main` 的 `c566e62` 起步。本条仅是候选源码，不是稳定包或线上发布。

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
- 重新运行 core 全量测试：456 passed、41 skipped；`quick_validate.py` 通过，`git diff --check` 通过。PR #41 由草稿转待评审以触发 CI；CI 结果、评审与 Release 尚需单独核实。
- 用本分支校验器检查生产协同候选 `subsystem.json`：0 项错误；同一 Manifest 经 SaaS 候选校验器接受，子系统只读 Action 的模拟业务快照结果也经 SaaS `AssistantCheck` 模型接受。这是跨仓**本地契约验证**，不是真实员工授权、企业服务器 Action 或在线提醒验收。
