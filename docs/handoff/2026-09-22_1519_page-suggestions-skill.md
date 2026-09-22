# 当前页面业务提示：Skill 与模板候选

## 范围

- 任务：当前员工当前页面的真实业务建议，用户选择后进入唯一 SaaS 助手草稿；Codex 子任务 `page_suggestions_skill`，认领基线 `bb7101a`。
- 规则依据：主任务本轮获取的 `zhuojian-server-deploy` `43dff14`、仓库与 core Skill 的 AGENTS。
- SaaS 主责：来源绑定、授权预检、提示呈现、替换/撤回/过期、草稿与确认；此记录不代替 SaaS 测试。
- Skill 本次：可选协议文档、模板适配器、Runtime 非敏感发现白名单、行为测试。根 TASKS/AGENTS、版本、发布包和稳定安装未改。
- 子系统：真实业务检查与依据仍由其后端产生，记录权限和写入保护不变。未修改或部署任何业务子系统，不声称款号错配已修复。无需给所有页面加提示。

## 实现

新增 `references/assistant-page-suggestions.md`，由 SKILL、business-ai-delivery 与 assistant-entry-bridge 路由；模板 AGENTS 记录最小接入边界。保留 2.4/2.5，不新增模型或后台执行身份。

`createAssistant` 增加 `supportsSuggestions()` 与 `suggest({moduleKey,pageKey,context,suggestions})`：

- 仅可信父窗口/精确 Origin/应用/nonce 的 `assistant-suggestions.v1` 协商后启用；返回无权或旧平台时保留人工功能。
- 请求最多三条、UTF-8 16 KiB，context/item 严格白名单、安全 JSON 深度/数量和字符串界限；来源字段回显现有 context，不引入 URL/模型/审批/自动发送字段。
- `accepted + received` 只表示提示接收，绝不串联 open、模型、Action 或业务写入。
- 严格匹配回执类型、请求、模块、页面与受控状态/code；未知 code、额外字段或错来源忽略。
- 新 suggest 可以替换旧 suggest 等待，取消旧 timer/promise；`[]` 能立即撤回；迟到回执无效。仍不抢占显式 open。超时不自动重试，dispose 清理。
- 复用 open 的边界与共享请求封装，既有 draft-only 行为测试仍通过。

Runtime sanitizer 增加 `features.assistantSuggestions` 五字段白名单；后端省略该可选字段或显式 unsupported 时输出 `{supported:false}`。已声明 supported 但缺少/改变 version、capability、authentication 或 mode 时结果 unknown、拒绝成功，不吞掉危险语义。后台委托/无人值守继续 false；不触碰 Runtime 部署流程。

## 验证

从 `skills/core/zhuojian-subsystem-builder` 执行：

```text
python -m pytest tests/test_navigation_adapter.py tests/runtime_host/test_platform_capabilities.py tests/test_ai_delivery.py -q
python -m pytest -q
python C:/Users/王鑫涛/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
git diff --check
```

- 聚焦：**102 passed，1.62 s**；其中 Node 测试运行真实模板 JS，不是协议字符串匹配。
- 全量：**344 passed，41 skipped，25.68 s**。跳过为既有 Windows/生成项目等环境受限项；未把 skip 计入通过。
- Skill quick_validate 通过；diff check 通过；四份改动 Markdown 的全部本地链接可解析。
- 模板行为覆盖两能力独立协商、身份伪造、context/item/UTF-8 边界、受控回执、替换与撤回竞态、open 互斥、迟到回执、超时、销毁、独立模式与无自动执行。
- Runtime 测试全部使用隔离响应，不联网；覆盖新声明、旧后端缺字段、不支持、非法声明与嵌套白名单去秘密。

这些结果不能代替真实两服务器、有效员工角色、业务检查结果、真实模型、确认写入及手机真机验收。SaaS 与模板的跨仓实际适配器测试及浏览器集成证据由主任务另外记录。

## 发布及下游

仅本地候选修改和测试，未推送、未合并、未发布稳定包、未部署 Runtime/SaaS/子系统；core 仍为 1.1.18。既有旧平台与独立页面保留人工路径。

发布需先 SaaS 前后端验证，再发稳定 Skill；需要当前页面提示的子系统由获授权开发者适配真实检查结果和上下文。模板更新不会自动部署现有子系统；业务错误可独立修复，不需等待该提示功能。发布时按跨仓规则补 wiki/下游通知，不在本子任务擅自发布或开外部写操作。
