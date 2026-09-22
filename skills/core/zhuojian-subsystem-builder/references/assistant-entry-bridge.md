# 业务目标进入统一助手

适用于页面中“检查缺项”“解释风险”“帮我处理当前记录”等真实业务入口。不要给每个页面机械增加聊天框。此协议只将用户主动选择的目标带入**同一个 SaaS 助手的可编辑草稿**，不是后台任务、模型调用、审批授权或业务执行接口。

由真实业务检查结果主动显示建议、供员工选择的场景，另按 [当前页面的业务提示](assistant-page-suggestions.md) 使用 `assistant-suggestions.v1`；接收建议不等于本协议的 draft_ready，不能串联自动 open 或发送。

## 两台服务器的分工

- 子系统服务器保存业务数据、规则、记录版本和业务流程，既有页面按钮与 Action 共用业务服务。
- SaaS 服务器保存 Task、AgentRun、LangGraph 检查点、审批和审计，统一管理供应商及模型。员工发送后，主脑按有效授权选择工具；需要业务数据时通过登记的 HTTPS Action 和短时签名身份调用子系统。执行前仍重新授权。
- 浏览器通过有界、验源的 Bridge 交接目标及当前页面引用。既不共享数据库/文件系统，也不交换 root、模型 Key、完整对话或供应商配置。

## 核对实际支持

这份文档和模板是接入约定，不是部署证明。新增能力的发布顺序仍是 SaaS 实现并验证 → 发布 Skill → 有需要的子系统适配。新旧 `contractRevision=2.4/2.5` 保持不变。

Runtime 安装了新命令后，开发 AI 可运行只读 `zhuojian-runtime platform-capabilities`。它使用既有受控 Runtime 身份访问固定 `GET /api/v1/ecs-publisher/platform-capabilities`，不要求业务负责人提供 SaaS 管理员或模型密钥。旧 Runtime 没有此命令、旧 SaaS 返回 404、网络/权限失败都记录为未核实，不能猜成支持；不要为此自动部署或轮换服务器凭据。

返回的是该后端实现的协议能力，不是当前员工授权，也不证明前端版本已同步、子系统已适配或模型实时可用。企业启用及员工授权仍须真实会话验证。`backgroundDelegation` / `unattendedExecution` 为不支持时，保留人工发起方式，不用 cron、模拟用户或 Runtime 凭据创建 AgentRun。

浏览器仅在当前可信 `zhuojian:host-ready.capabilities` 含 **`assistant-open.v1`** 时启用入口。来源、父窗口、应用与本次 `launch_nonce` 必须匹配；不能凭 Skill、Manifest 或后端版本代替这次握手。

## 请求与回执

先通过已有 `zhuojian:context` 上报当前模块、页面、实体、筛选、选择和版本。业务引用只是提示，不是已验证事实或写入授权；不要包含整表、凭据或无关个人资料。

用户点击业务入口时发送：

```json
{
  "type": "zhuojian:assistant-open",
  "version": 1,
  "application_slug": "sample-review",
  "launch_nonce": "本次启动 nonce",
  "request_id": "assistant-request-0001",
  "module_key": "sample_review",
  "page_key": "sample_review.list",
  "goal": "检查当前选中评审记录的缺项，给出补齐建议；需要修改时先让我确认。"
}
```

只允许上述字段：目标非空且不超过 2,000 字符，整包不超过 16 KiB；请求号为 8–120 个安全标识字符，模块最长 120、页面最长 160。不接收模型、供应商、Action 参数、执行 URL、角色、审批决定或自动发送指令。目标文字仍是非可信业务输入，不可覆盖平台规则。

SaaS 校验当前 iframe、精确 Origin、nonce、模块/页面匹配后，以当前员工会话调用内部预检 `POST /api/v1/terminal/applications/{application_id}/assistant-entry`，核对生效 Manifest、页面和当前 AI Action 授权。这个接口不交给子系统持有会话令牌，不创建 Task、AgentRun 或执行业务。预检成功后仍要检查页面未切换、用户未开始输入。

回执 `zhuojian:assistant-open-result` 包含相同版本、应用、nonce、请求号、模块及页面：

- `status=draft_ready`：目标已进入可编辑草稿，**模型和业务均未执行**。不显示“任务完成”。
- `status=rejected` 与受控 `code`：保留原业务页面与原有助手内容。不得根据错误文字扩大权限或直接改用通用助手执行原业务目标。

SaaS 保留已有对话、附件和草稿；正在运行、待审批、录音/语音或草稿冲突时不覆盖。相同请求的重放不追加、不重复执行；返回中不包含 Task、历史、文件或模型信息。接收后切换页面/实体/筛选/版本时，草稿来源必须保留并阻止错绑发送；刷新丢失绑定时也不能把原目标当作无来源的普通草稿发送。

## 模板调用

可复用 `static/zhuojian-assistant.js`，在发送 ready **之前**初始化监听器。配置只从可信后端 bootstrap 取得，不从任意查询参数取得：

```javascript
const assistant = createAssistant({ applicationSlug, launchNonce, platformOrigin });
// 用户点击真实业务入口后；先上报与当前页面一致的 zhuojian:context。
await assistant.open({ moduleKey, pageKey, goal: '核对当前记录并提出处理建议' });
// 此处只能提示“已带入助手，请核对后发送”，不能提交业务或显示已完成。
```

组件卸载时 `assistant.dispose()`。不支持或独立访问时显示明确限制，保留人工操作；不拼 SaaS 内部路由，不打开另一套助手。超时表示回执未知，应先检查助手现有草稿，不自动重试。业务负责人不需要解释协议，开发 AI 负责适配与错误反馈。

## 沿用执行和结果链路

员工在统一助手中编辑并发送后，沿用现有 Task、授权能力搜索、工具容错和 LangGraph。需确认的写操作使用原确认/拒绝卡片，不能把点击业务入口当成审批。签名 Action 在子系统服务端验证数据范围、版本和幂等；结果未知先核实，不盲目重发。成功写入后的刷新继续使用已有可信 `tool_result → zhuojian:refresh`，不凭交接回执刷新、重载或制造成功。

## 验收

至少在桌面和手机验证：真实业务按钮 → 同一助手显示目标及来源 → 点击发送前没有 Run → 发送后沿原授权工具链；再验证旧平台、错来源/iframe/nonce、无权及撤权、重复请求、已有草稿/附件/审批/录音、预检中切页或输入、接收后实体变化、刷新恢复和回执超时。写入闭环另用获准测试数据验确认/拒绝、回执和局部刷新。

分别记录平台后端实现、前端协商、员工授权、子系统适配及部署；本地适配器测试不代表两台线上服务器已经联调。
