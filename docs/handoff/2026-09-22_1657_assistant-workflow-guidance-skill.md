# 业务流程知识与当前页提醒：Skill 候选交接

## 范围与状态

- 日期：2026-09-22，北京时间。
- 工作树：`zhuojian-skills-workflow-20260922`；分支 `codex/assistant-workflow-skill-20260922`；基线 `a55fa00`。
- 责任：本次仅 Skill 规范、JSON Schema、共享校验、Runtime 模板白名单、通用契约 fixture 与本地测试。SaaS 后端/前端由同任务其他工作树实现；业务检查及真实流程由各子系统负责人后续适配。
- 已修改、已本地测试；未推送、未发布 Skill、未改稳定安装、未部署 Runtime/SaaS/子系统。本文件不是上线证明。
- 保留 `contractRevision=2.4/2.5`、`skillVersion=1.1.18`；子任务未改根 `AGENTS.md`、`TASKS.md`，主树集成后的文档维护见末尾补充；未改版本号或发布包。

## 实现

1. 可选 `aiSemantics.workflowGuides`：闭合字段，最多三流程/八步骤，业务目标、前提、完成证据、异常；同 Manifest 真实页面/Action 引用、键唯一、整体紧凑 UTF-8 JSON ≤32 KiB。步骤模块键 ≤120，页面/Action ≤160。元数据只说明通常做法，不能证明实时业务阶段或成为执行 DSL。
2. 可选 `proactiveCheck`：当前页面已登记、AI 可用、无确认、无专业模型能力的只读 query；间隔 60..600 秒，省略为90。参数根仅必填 `context`，业务上下文白名单；员工与数据范围来自签名身份。仅合法声明的专用检查豁免普通 v2.5 query 的顶层 limit 规则，其他查询不变。
3. `assistant-check-result.schema.json` 与 `validate_assistant_check_result`：实际 `result.assistantCheck` 闭合四字段、版本严格整数1、真实摘要/版本、有界建议、ID 唯一、对象整体紧凑 UTF-8 ≤16 KiB；completed/空对象/失败不等于检查成功。JSON Schema 的字面 `$ref/allOf` 表达不被硬编码拦截，运行时仍必须验证实值。源码/端点校验不会冒用 Runtime 凭据查询员工业务数据。
4. Runtime optional `assistantWorkflowGuidance` 六字段白名单，与 SaaS 同任务协商一致。旧后端缺字段投影 `supported:false`，错误响应为 unknown，不伪称支持；保留后台委托/无人值守为不支持。
5. 新参考从 Skill、业务提效、平台契约及原生模板指令路由；明确业务负责人只确认业务事实，不设计接口。SaaS 按权限投影整条流程，员工开启且当前页可见时只读检查，不创建 Task/Run、不调用模型/自动写。真实建议仍由员工选择进入唯一助手草稿，发送后沿原权限与确认执行。
6. `action.aiTool` 六项说明消费与 SaaS 约定一致：示例仅投影 `userRequest`，不把示例 `params`/ID 当本轮目标；字段仍是可选、非可信说明，不是权限或审批策略。
7. `tests/fixtures/workflow-guidance.manifest.json` 是完整合成契约输入，非生产配置且无业务处理器。普通脚手架不自动登记虚构检查。开发 AI 必须根据真实代码/样表/业务口语实现有价值的流程与检查。

## 验证

在 canonical core 目录执行：

```text
python -m pytest -q tests/test_workflow_guidance.py tests/runtime_host/test_platform_capabilities.py tests/test_manifest_schema_versions.py tests/test_validate_source.py tests/test_generated_native_template.py tests/test_ai_delivery.py
```

结果：**241 passed in 15.08s**。包括真实 JSON Schema、共享语义校验、`validate_source.py` 子进程入口、2.4/2.5 可选缺省兼容、查询 limit 豁免边界、相同/跨模块真实引用、闭合/超限/重复键/大小、只读与固定上下文、检查结果、Runtime 真函数白名单/旧响应兼容、脚手架与本地交付资料回归。

```text
python C:/Users/王鑫涛/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/core/zhuojian-subsystem-builder
git diff --check
```

均通过（Git 仅提示工作树行尾转换警告）。未运行 updater、共享安装、Release 构建、网络请求或任何线上查询。全套回归和 SaaS/Skill 跨仓真实 fixture 验证由主任务集成后执行，本交接不提前宣称通过；未进行真机、真实员工或跨服务器业务验收。

## 集成与发布责任

- 主任务合入后补根任务记录、项目说明与组织 wiki；可概括为“可选流程说明及显式开启的当前页只读检查，无后台 Run，无契约迁移”。
- 先验证并部署匹配的 SaaS 后端/前端，再发布 Skill；Runtime capability 命令需要新模板部署才会输出新字段，单独更新本地 Skill 不会更新服务器命令。
- 现有子系统只有实现真实检查/登记流程、通过当前员工权限和数据范围验收后才可使用新增能力。未改的旧系统继续原功能；不声称生产协同 Excel 款号错配因此已修复。
- 在目标环境验证：未开启不查、可见页获权查询、隐藏/关闭/切页/撤权取消旧来源、真异常/无异常/失败分离、无自动 Run 或写入、建议选择到同一助手草稿、实际写入确认/拒绝、桌面及移动端提示可用。

## 回退

本次字段可选。未启用页面可移除新增字段并保留既有页面与 Action；平台不支持时保留人工功能。任何运行时回退由主任务针对已部署版本执行，不回滚业务数据，不改变员工权限，不使用另一个模型或子系统自建聊天绕过平台。
## 主树复核补充

候选已在主工作树 `zhuojian-skills-assistant-bridge-20260922` 集成为 `068a073`。使用既有 Python 3.12 环境从 core 目录执行 `python -m pytest -q --tb=short`：421 passed、42 skipped、109 subtests passed；存在 Starlette 的既有 httpx 弃用警告，不修改依赖。跳过项不计通过，完整业务流程、真实员工、跨服务器、真机及真实 Redis 多 Worker 未在本轮验证。主树补充不是稳定发布；未推送、未安装、未部署。

SaaS 主树新增 `tests/test_workflow_skill_contract.py`，通过 `WORKFLOW_SKILL_SOURCE` 直接加载本候选 fixture、共享校验器和 Runtime 函数：21 项跨仓测试通过，包含在 SaaS 263 项聚焦回归内。正向 2.4/2.5、越权/可执行/超限声明拒绝、检查结果一致性，以及实际平台能力输出的 Runtime 白名单投影均通过。2.4 fixture 必须同时采用其既有 HS256 auth，不能只将 2.5 的 revision 改名；未放宽 SaaS 登录校验。此处测试是静态契约与隔离函数联调，不代表 Runtime 或业务服务器已安装新版。
