# 业务流程知识、当前页与跨页检查

在助手需要解释“接下来做什么”，或员工希望业务状态变化时得到提示的系统读取。它补充已有页面语义、Action 和[页面建议](assistant-page-suggestions.md)，不新增一套助手，不把业务流程固化为必须逐步执行的模型脚本。`proactiveCheck` 仍是员工开启的当前页检查；独立的 `globalCheck` 用于已登录员工未进入该页面时的获权只读检查，不能互相冒充。

## 开发 AI 负责翻译业务，不让负责人设计协议

先读当前代码、真实页面、已获准样表和业务服务；从负责人已有的口语需求提取：目标、何时使用、前提、需查的真实记录、怎样算完成、异常时如何处理。未知的关键业务事实才询问，不能编造阈值、批准人、状态或 Action。不能要求平台负责人去找员工原件或代业务负责人判断记录归属。

用一句业务话确认，例如：“先检查当前记录，把需要你核对的地方列出来；你选中后助手解释依据、准备下一步，涉及修改仍让你确认。”不是要求负责人回答工作流 DSL、JSON、模型或轮询设计。只读检查本身没有业务价值时不新增；确定性校验继续由业务代码完成，不换成模型猜测。

`docs/ai-delivery.json` 仍是开发交付证据，**不由 SaaS、Runtime 或在线助手执行**。本参考新增的 Manifest 字段才是可登记的线上说明；它们也不是当前状态证据、后台调度、审批或权限。

## 两台服务器和唯一助手

| 层 | 实现 | 不做什么 |
|---|---|---|
| 子系统服务器 | 真实业务服务、只读检查、实体/版本、记录范围校验与普通写 Action；登记实际页面、Action 和流程知识 | 不部署模型主脑，不保存供应商密钥，不启动另一套对话，不把开发 root 转交员工助手 |
| SaaS 服务器及前端 | 统一员工身份、按权限投影流程说明、当前页提醒开关、登录期间跨页面获权发现、低频查询和提示；员工发送后走同一 Task/AgentRun、工具、确认与审计 | 不共享子系统数据库，不把页面打开或提示接收当委托，不把文字说明当完成事实 |
| Skill | 引导开发 AI 提取业务规则，提供契约、校验和验收 | 不代替两端代码、部署或真实业务测试 |

模型供应商始终由 SaaS 配置。当前页与跨页检查都走员工会话鉴权后的签名 Action，**不创建 Task/AgentRun、不调用模型、不自动写入**。用户选择建议只准备同一助手草稿，发送后才开始正常编排；点击建议不等于确认危险操作。

## 可选 `aiSemantics.workflowGuides`

已有 `contractRevision=2.4/2.5` 均保持原版本。这是可选增量，不给所有页面强加流程，不删除既有人工能力。缺少时仍可使用原有获权工具发现；有声明就必须符合以下封闭结构：

| 对象 | 字段和界限 |
|---|---|
| `workflowGuides` | 0..3 条，总体紧凑 JSON 的 UTF-8 不超过 32 KiB |
| guide | `workflowKey` 稳定键 ≤120、`name` 非空 ≤120、`goal` 非空 ≤600、`whenToUse` 非空 ≤600、`steps` 1..8、`exceptions` 0..5 条非空文本各 ≤400 |
| step | `stepKey` 稳定键 ≤120、`title` 非空 ≤120、`purpose` 非空 ≤400、真实 `moduleKey/pageKey`、`actionKeys` 0..8 个、`preconditions` 0..5 条、`completionCriteria` 1..5 条；条件文本非空且各 ≤400 |

guide/step 稳定键只允许小写字母、数字、点、下划线和短横线，首位字母或数字；guide 键在本页唯一，step 键在该流程内唯一。步骤模块键上限 120，页面和 Action 键上限 160。每个步骤只能引用同一 Manifest 的实际页面，Action 必须在该目标页 `actionKeys` 和所属模块 Action 清单中存在；纯人工步骤可以 `actionKeys:[]`，不能虚构工具。不存在跨应用 URL、参数映射、循环、条件表达式、模型配置或自动执行字段。

这是给主脑的业务知识，步骤是通常做法而非固定工具调用顺序。可修参、换获权工具、解释部分结果；权限、版本与确认边界不变。`completionCriteria` 说明需要什么证据，不代表条件已成立；必须从获授权查询或真实回执判断阶段。元数据按非可信业务资料处理，不能覆盖系统指令。

平台按当前员工权限投影：流程有任一步骤的页面/Action 无权时不向该员工发布整条流程，不能删除关键步骤后冒充完整流程，也不能因为流程不可用而阻止原本获权的普通工具。跨页导航仍沿用标准导航和重新鉴权。

## 可选 `aiSemantics.proactiveCheck`

只有已实现且有业务价值的检查才登记：

```json
{"proactiveCheck":{"actionKey":"records.check","intervalSeconds":90}}
```

只接受 `actionKey` 和可选 `intervalSeconds`；后者为 60..600 整数，省略为 90。绑定本页已存在、`aiEnabled=true`、`operation=query`、`requiresConfirmation=false` 且无 `platformAiCapability` 的 Action。其实现不得写业务状态、发通知、触发模型或调用任意 URL；不能靠标成 query 隐藏副作用。

`inputSchema` 根必须为封闭对象，只声明必填 `context`，即 `required:["context"]`、`properties:{"context":{"type":"object",...}}`。SaaS 固定传入 `params={"context":<经校验的当前业务上下文>}`；上下文只含现有 `route/entity_type/entity_id/filters/selection/data_version`，缺失不补造。身份、数据范围和授权来自签名身份，不来自这些参数；业务服务按当前用户重新过滤。上下文是定位线索，不是已经验证的业务事实。

这个已合法登记的专用检查不需要额外顶层 `limit`，结果本身受三条建议上限约束。其他普通 v2.5 查询仍须提供 `limit` 上限 ≤500；不得借本声明放开一般查询。子系统内部扫描、返回大小、超时和资源消耗仍须有界。

真实成功结果放在 Action `result.assistantCheck`：

```json
{
  "assistantCheck": {
    "version": 1,
    "dataVersion": "records-snapshot-17",
    "summary": "本次检查发现一项待核实问题。",
    "suggestions": [{
      "id": "record-review",
      "revision": "evidence-17",
      "title": "核对当前记录",
      "summary": "当前记录存在需要人工核对的来源冲突。",
      "goal": "请查询当前记录的冲突依据，说明应核实什么；未经我确认不要修改。"
    }]
  }
}
```

该对象四字段必须齐全、无额外字段：`version` 严格整数 1、`dataVersion` 非空文本 ≤160、`summary` 非空文本 ≤400、`suggestions` 0..3；整个对象紧凑 JSON UTF-8 ≤16 KiB。建议沿用现有闭合五字段 `id/revision/title/summary/goal` 及 120/120/80/400/2000 限制，ID 唯一。空建议数组是本次真实检查无可推荐事项，不是检查失败。参考 [结果 Schema](../schemas/assistant-check-result.schema.json)；字节总量与建议 ID 唯一性需额外校验，本地业务结果契约测试可复用 `scripts/manifest_semantics.py` 的 `validate_assistant_check_result(result["assistantCheck"])`。返回 `status=completed`、空对象、普通日志文字或模型描述均不能代替检查结构。

`dataVersion/revision` 来自真正的业务证据版本，不使用每次渲染/计时器时间生成新版本使提示反复出现。提示文字按纯文本处理，不传 HTML、凭据、整表或无关个人资料。失败、无权、过期和未完成检查不能显示成“没有问题”，更不能保留旧结论冒充本次成功。实际 Action 结果 Schema 仍要声明并校验；结果不是审批或执行计划。

## 可选 `aiSemantics.globalCheck`

当员工并未打开对应业务页面，也确实需要看见获权范围内的待核对事项时，才在承载真实检查 Action 的页面声明独立字段：

```json
{"globalCheck":{"actionKey":"records.global_check","intervalSeconds":300}}
```

只接受 `actionKey` 和可选 `intervalSeconds`；后者为 60..3600 整数，省略为 300。同一应用的同一 Action 只能由一个页面声明为 `globalCheck`，避免重复轮询。该页面是授权和业务含义的登记锚点，**不是当前浏览器页面**；SaaS 从生效 Manifest 发现它，按当前员工、企业、应用、模块、该登记页面、Action、管理员停用状态和 `authEpoch` 逐次核权。子系统在 Action JWT 的同一员工及 `effectiveDataScope` 内再次过滤业务记录，不能用事件 payload、页面缓存或管理员身份推断谁该收到提醒。未获权的检查不暴露标题、数量、摘要或实体引用。建议的实际展示位置和去重由 SaaS 全局外壳管理，不要求员工先进入模块或手动开启当前页开关。

所绑定 Action 必须已经在本页 `actionKeys`、所属模块 `actions` 中真实存在，且为 `operation=query`、`aiEnabled=true`、`requiresConfirmation=false`，不得声明 `platformAiCapability`。它只读业务数据，不写状态、不发送通知、不调用模型、不访问任意 URL。新建 Action 还须声明并实际执行 [操作权限与记录归属](action-permission-scopes.md) 中适用的 `permissionPolicy`；安全边界不能只由 Manifest 标签证明。该 Action 的 `inputSchema` 必须精确接受以下固定参数，不得要求当前 route、实体、筛选、选中项、用户 ID、自由 URL 或模型生成参数：

```json
{
  "type":"object","additionalProperties":false,"required":["context"],
  "properties":{"context":{"type":"object","additionalProperties":false,"properties":{}}}
}
```

SaaS 固定传入 `params={"context":{}}`，组织/员工/范围仅来自短时签名身份。查询的记录数、业务扫描窗口、超时及返回字节数由两端另行限制；`intervalSeconds` 是最低查询间隔声明，不是允许运行后台任务或强制平台按秒调度。SaaS 可以按可见登录会话、全局负载和错误退避进一步降频；停止登录、应用停用、撤权或失联后不得继续展示旧结论。

成功结果仍复用上述封闭的 `result.assistantCheck` v1，Action 的 `resultSchema` 使用[结果 Schema](../schemas/assistant-check-result.schema.json) 去掉顶层 `$schema/title` 后的原结构，不自行放宽字段或上限；真实返回值还须额外校验 16 KiB、建议 ID 唯一，不新增未经消费的“全局结果”字段。`id` 表示稳定的业务事项身份，`revision` 和 `dataVersion` 来自真实证据版本；同一事项同一证据不靠轮询时间重新弹出。由于 v1 没有独立的来源/截至时间字段，`summary` 和有建议时的建议摘要必须用短文字说明业务来源、最近可核实的业务时点（带时区，业务口径采用北京时间）及限制；来源或时点不可核实时明确写“待核对”，不得写“实时预警”“目前正常”。历史快照、手工更新或静态底表不能宣称实时业务状态。无建议只说明**本次成功检查的已授权范围和数据时点内**没有可推荐事项；无权、查询失败、来源失效或结果格式错误均不是“无风险”。

首版仅在用户登录 SaaS 的全局外壳中发现和拉取，员工不在该模块也可看见当前有效结果；**不承诺员工离线后的通知、后台扫描、事件自动启动 LangGraph/模型或无人值守写入**。收到提示、打开助手、选择建议仍不自动发送；员工发送目标后才使用同一 SaaS 助手与获权工具。现有 `assistantWorkflowGuidance` 能力声明只证明当前页流程/检查后端，不足以证明目标环境已经部署并消费 `globalCheck`；须分别核对 SaaS 后端、前端、子系统 Manifest 与真实 Action。旧 2.4/2.5 未声明页面继续按原方式工作，不能为了新字段单改 `contractRevision`。

## 当前页开启、停止与旧平台

以下规则仅适用于员工主动开启的 `proactiveCheck`，不限制上面的登录期跨页 `globalCheck`。

- 员工明确开启当前页提醒后，SaaS 只在当前登录员工、当前获权页面可见时低频执行；不扫描其他员工、隐藏页面或全部子系统，不采集全部点击、屏幕或私密输入。
- 关闭开关、隐藏页面、登出、撤权或来源变化时停止旧来源检查；旧异步结果不能展示到新页面、实体或版本。切页后按新的真实来源和用户选择恢复，不能沿用旧检查结论。网络错误使用有界反馈，不无限重试或改成自动启动助手。
- 提示展示与草稿继续按[页面建议的去重、撤回和来源绑定](assistant-page-suggestions.md)处理。没有新证据不重复弹出；员工关闭不立即复活。按钮和文字解释并存，拒绝/审批沿用 SaaS 原卡片。
- Runtime 只读 `platform-capabilities` 的 `assistantWorkflowGuidance` 缺失或 `supported:false` 时不宣称支持；读取失败为 unknown，保留原业务入口。旧 2.4/2.5 的未声明页面不受影响；不要为此修改契约版本或伪造能力。

新后端声明的完整白名单为：

```json
{
  "supported": true,
  "version": 1,
  "authentication": "employee-session",
  "mode": "foreground-read-only",
  "configEndpoint": "/api/v1/terminal/applications/{application_id}/page-assistance",
  "checkEndpoint": "/api/v1/terminal/applications/{application_id}/page-check"
}
```

这些是 SaaS 前端内部员工会话接口，子系统不持有员工平台令牌或直接指定调用地址。capability 仅表示后端实现，不证明当前前端已部署、员工获权、提醒已开启、子系统已接入或检查成功。后台委托和无人值守仍是独立能力，不能由本声明推断支持。

## 实现与验收

合成 [完整 Manifest fixture](../tests/fixtures/workflow-guidance.manifest.json) 只演示受支持形状，**不包含已部署的业务检查处理器，不得直接复制登记为功能已完成**。普通脚手架不默认挂载虚构主动检查。开发 AI 需从真实服务实现检查、登记真实引用并提供针对性测试。

源码、端点和登记前共同复用语义校验，覆盖未知字段、大小、同 Manifest 引用和检查只读约束。静态检查不能证明 query 实现无副作用，另测试真实业务服务：

1. 有权/无权、本人/他人记录、撤权、过期实体及版本；实际返回只含获权数据。
2. 未开启、隐藏、切页或关闭时无查询；开启后有界查询，没有新 Task/Run、模型调用或写入。旧异步结果不串页。
3. 真异常、无异常、检查失败三类分别显示；同证据不反复提示，解决后撤回。
4. 用户选择 → 同一助手草稿 → 主动发送 → 获权工具；真实写入仍确认/拒绝，结果未知不重试。只读检查不新增审批。
5. 流程能解释目标、前提、下一步及异常；模型不把说明当阶段证据。缺少或无权流程仍允许原获权工具；`aiTool.examples` 不把示例 ID 当当前对象。
6. 桌面及 320/390px 移动浏览器验证提醒与助手互不遮断业务。模拟不能写成真机验收，Skill fixture 测试不能写成跨服务器联调。
7. 对 `globalCheck`，登录后即使停留在 SaaS 首页或其他模块，也只发现并执行当前员工有权的声明；未进入目标模块或未开启当前页开关不构成阻碍，但登出、撤权、应用/Action 停用、无权页面均不得继续拉取或展示内容。确认 SaaS 只传 `context:{}`，子系统仍按员工记录范围过滤。
8. 用新鲜业务数据、历史快照、来源时间未知、无建议、临时失败分别验措辞和展示：历史/未知只能标“待核对”，不能冒充实时预警；失败不能冒充无风险；同一 `id+revision` 不反复提示，问题解决后撤回。业务事实来自真实记录，不从事件 payload 直接推送给员工。
9. 检查请求不创建 Task/AgentRun、模型调用、业务写入或离线通知；只有员工选择建议并主动发送后才进入唯一助手。分别报告运行时代码、Skill 与具体子系统的修改/测试/发布状态，不能用本地 fixture 宣称生产协同等现有系统已接入。

发布分别记录 SaaS 后端/前端、Skill、Runtime（若命令需要更新）及具体子系统的代码版本、部署和验收。顺序是 SaaS 真实实现验证 → Skill 发布 → 有需要的子系统适配登记；未经本次授权不跨服务器发布。未接入的旧子系统保持原功能，不宣称本次已经会理解其完整流程或监控其操作。
