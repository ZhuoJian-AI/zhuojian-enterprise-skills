# 跨服务器统一助手入口（候选）

## 任务与边界

2026-09-22，Codex，ASSISTANT-OPEN-BRIDGE-20260922。关联 SaaS Issue #356。本工作树基线 `70c7753`；SaaS 配套工作树 `ai-platform-assistant-bridge-20260922` 基线 `ebc2ac1`。

- SaaS 主责：员工授权预检、同一助手草稿、来源绑定与恢复、已有模型/确认/远端 Action 编排。
- Skill：新增入口协议、浏览器适配器、Runtime 只读能力核对命令和测试，不另建在线助手。
- 子系统：业务规则、数据、实体引用和 Action 保持原服务器。三个现有系统未修改、未登记、未部署。只有需要新的页面业务入口时，后续才按真实协商结果适配；不共享数据库/文件系统/模型密钥。

## 候选内容

`references/assistant-entry-bridge.md` 定义 `assistant-open.v1`：先发当前 context，用户点击后仅带入目标草稿；来源变化、已有输入、审批或运行时不覆盖。`draft_ready` 不等于执行成功；原远端 Action/确认/刷新链路不变。新模板附可复用 `static/zhuojian-assistant.js`，不强制给所有页面增加无业务价值的 AI 按钮。

`zhuojian-runtime platform-capabilities` 使用受控 Runtime 身份访问固定 SaaS 端点，拒绝重定向，只投影非敏感能力。缺命令、404、鉴权失败或未知 Schema 都不能当支持；员工授权与浏览器前端协商必须另外验证。Runtime 凭据不允许启动员工 Run。

后台事件/定时创建 AgentRun、长期离线委托仍未实现，不以新入口或 LangGraph 恢复冒充。专业 `ai-run` 与新入口不混用：前者生成结构化草稿，后者交给现有用户助手。

## 验证

在 `skills/core/zhuojian-subsystem-builder` 执行：

- `python -m pytest -q`：331 passed、41 skipped，25.71 秒。
- `python -m pytest tests/test_navigation_adapter.py tests/test_generated_native_template.py -q`：6 passed，9.39 秒。
- Skill `quick_validate.py`：通过；`git diff --check`：通过。
- 浏览器适配器实际 JS 测试覆盖能力协商、Origin/source/nonce、输入限制、只接收草稿回执、冲突、超时和销毁，不访问真实 SaaS。
- Runtime 子任务 120 passed / 1 skipped，详见 [命令交接](2026-09-22_runtime-platform-capabilities.md)。
- 独立跨仓检查直接调用 SaaS 候选 `platform_capabilities_endpoint`，将实际函数输出传给 Skill `sanitized_platform_capabilities`：完全相等；不是复制 fixture，对外网络请求为零。该测试不代替真实员工登录及两台线上服务器联调。

41 项跳过包含 Windows 不适用或需生成项目环境的已有项目测试；本次未为补证更改线上授权或业务。完整真实业务写入、真人手机、真实 Runtime 请求尚未验收。

## 发布状态

候选已推送为 [draft PR #35](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/pull/35)，配套 SaaS 为 [draft PR #358](https://github.com/ZhuoJian-AI/ai-platform/pull/358)。均未合并，不是稳定 Release；不能把 draft 跳过 CI 当作云端测试通过。版本元数据保持已安装基线 core 1.1.18，不提前占用新版本，不修改本机已安装 Skill。不推送/发布 Runtime 安装器到任何 ECS。后续先完成 SaaS 构建、受控部署与线上验证，再发布递增版本的稳定 Skill，最后由有权限的子系统负责人适配和验收。代码、推送、部署与实际启用分别报告。
