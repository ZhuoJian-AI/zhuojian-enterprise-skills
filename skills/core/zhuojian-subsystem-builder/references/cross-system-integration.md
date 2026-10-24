# 跨系统对接与受控配置

适用于两个应用或模块之间传递业务数据、移动上传入口或共享办理结果；既包括同机/跨机，也包括同一应用的不同模块。仅页面导航仍按 navigation Bridge；已有同模块内部调用无需另建事件路由。本流程保持既有 2.4/2.5，不要求无关子系统升级。

## 先查真实链路，再分层实施

开发 AI 对完整结果负责：确认来源和唯一业务归属 → 查双方运行版本 → 实现真实数据传递与消费 → 提出精确配置计划 → 企业管理员在正常 SaaS 会话确认 → 原 Runtime 查询并应用获批范围 → 验收双方真实业务结果。SaaS 负责计划授权、定向投递和审计；子系统负责业务对象、文件、处理及结果；Skill 负责这套实施与验收流程。

1. 读取双方 Runtime/应用/模块身份和服务器当前源码，核对 Manifest、实际入口、事件、业务服务与已有配置。不能只看服务器健康或本地旧副本；同机不等于共享数据库授权。
2. 明确权威业务记录归谁、另一侧保存草稿/附件还是只保留提交凭据。“只在目标系统保存”不能实现成两边各存一份再声称一致；必要的临时文件、传输队列与持久业务记录要区分。
3. 保留通用资料与按业务编号资料等真实对象边界，使用稳定 ID 和版本映射。文件名、同名对象或“目标已存在”都不能代替归属核对；不确定匹配要供人核对，不能取第一个候选。文件流程同时按 [资料识别与对象归属核对](business-identity-review.md)。
4. 优先复用目标既有解析、保存和查询服务；页面与助手调用同一业务规则。每条链须有双方实际 Manifest/服务绑定、载荷与文件访问方式、可信操作者或明确机器委托、版本、幂等、失败和回执设计。不得直连另一业务数据库、共享应用密钥或以 root 身份冒充员工。

业务协议选型遵循项目已确认约束，使用真实获权 Action 或版本化事件；不能因为是跨应用就虚构平台未实现的接口。使用平台事件时，来源必须声明 publishes、目标模块明确 subscribes，事件应带目标真正可处理的数据或受控文件引用。只有名称/版本的“已保存”摘要不能冒充可导入文件；不能复制签名临时 URL、跨应用文件密钥或未获权对象来补数据通道。

## 业务处理和最终结果必须先做实

模板 `/api/integration/event-deliveries` 只提供验签、订阅校验、幂等收件和日志，默认返回 `accepted: true, processed: false`。它不会自动解析附件、创建业务记录或返回最终业务成功。开发 AI 必须接入目标真实服务，在业务写入、幂等结果和必要 outbox 之间保持一致；相同操作重放不得重复创建，ID 换内容须拒绝。

源端应区分待投递、已收件、已处理、失败及结果未知，并关联稳定提交标识、实际 deliveryId 与目标业务记录 ID/版本。目标要提供真实处理结果，源端采用既定受控回执事件或获权查询回读。平台 HTTP 200、`accepted`、事件日志存在或 AI 自称已完成都不能替代业务落库证据。长任务可以先收件，但在最终完成前不能展示导入成功；失败恢复先核对已成功结果，只重做未完成部分。

## 精确配置计划与管理员确认

Runtime 登记凭证仍只在企业/Runtime边界内工作，不获得通用管理权限。开发 AI 使用 `scripts/integration_plan.py` 提出计划、查询状态、应用已批准配置和核对投递证据；参数以 `--help` 及本节所列已发布平台合约为准。凭证只由脚本在原 Runtime 内部读取现有受保护文件，不写进参数、JSON计划、日志、仓库、交接或回复。

计划必须限定本企业的来源应用/模块、目标应用/模块、版本化事件类型和业务用途，不能带通配目标、任意 URL、角色变更、全局 Token 或数据库访问。原 Runtime 可以查询本企业目录并提出涉及自身应用的对接；跨 Runtime 的对端仍须完成已授权的代码与登记，不能据一个 Runtime 的服务器权限修改另一台服务器。

企业管理员通过 SaaS 正常登录查看具体来源、目标、用途与影响后确认或拒绝；一次业务聊天同意不等于平台已经保存授权。确认绑定精确计划与当前版本，变更范围、过期、停用、撤销或目录漂移后必须重新核对，原批准不能扩展成任意后续路由。

原 Runtime 查询状态并自动应用已批准且仍有效的精确范围。未批准、已拒绝/配置授权过期/撤销、Runtime 不匹配或目录未就绪时不应用；不索要业务负责人的主平台 root、管理员 Token，不扩大登记凭证，也不用数据库直写绕过确认。配置执行授权默认 72 小时、最多 7 天，仅限制何时可以应用配置；已建立的业务关系持续至明确撤销，不能把配置期限届满解释为已撤销路由。请求中断或结果未知时先用稳定计划/request ID 读回，不自动重新 POST；没有确定结果就保留未知状态并具体交接。

平台尚不支持计划接口或配置仍待确认时，继续双方已获授权的开发、测试和待发布准备，并在各项目 `docs/ai-delivery.json` 及脱敏交接列出：确切缺口、责任层、已完成部分、计划标识/状态、正常确认入口、验收条件和恢复下一步。未获权操作保持待执行，不泛称“找平台方开通”后结束全部工作。平台待办按 [业务提效设计与交付](business-ai-delivery.md) 提交，未提交不能称已受理。

## 平台接口与 Runtime 命令

仅在目标 SaaS 的获权 `platform-capabilities` 明确声明 `features.integrationPlans.supported=true`、`version=1`，且下述接口在目标环境实测可用时执行。脚本每轮先做一次获权能力发现；旧平台未声明或没有接口时返回具体 SaaS 缺口和“配置未启用”，继续已授权的双方准备与交接。Skill 文档和发布包不证明新接口已经上线，不得靠猜路径尝试绕过能力缺失。

在发起计划的原 Runtime 内运行，不把登记 key 复制到开发电脑或命令参数。默认读取 `/etc/zhuojian/runtime.json` 中的 `platform.baseUrl` 与 `deployment.registrationCredentialRef`；文件引用由 Runtime 提供。平台 origin 必须为 HTTPS，脚本不跟随重定向，也不在失败信息中输出服务器响应正文。

```text
python <skill>/scripts/integration_plan.py catalog
python <skill>/scripts/integration_plan.py propose --plan <本地脱敏计划.json>
python <skill>/scripts/integration_plan.py status --request-id <稳定请求标识>
python <skill>/scripts/integration_plan.py status --plan-id <平台返回的计划ID>
python <skill>/scripts/integration_plan.py apply --plan-id <计划ID>
python <skill>/scripts/integration_plan.py verify --plan-id <计划ID> --delivery-id <真实投递ID>
```

需要指定其他受保护 Runtime 档案时，将 `--runtime-profile <档案>` 放在子命令前；不能将它用于绕过平台对原 Runtime 的绑定。`apply/verify` 可加 `--version <平台版本>` 固定预期版本，省略时先读当前版本。脚本从不批准计划、不改业务角色，也不执行测试业务写入；管理员确认仍使用平台返回的 `approval_url`，由本人在正常企业管理会话中查看并确认。

计划 JSON 只包含以下字段；应用 ID、模块键和事件名从真实获权目录与双方代码确认，不照抄示例 ID：

```json
{
  "request_id": "document-transfer-20261024-01",
  "title": "提交资料并返回处理结果",
  "purpose": "从提交模块送至记录所有方处理，并显示真实结果",
  "data_description": "版本化结构化字段及获权文件引用；不含密钥或原始业务数据",
  "ownership_description": "目标拥有业务记录，来源只保留提交和最终结果引用",
  "edges": [
    {
      "key": "submit",
      "kind": "forward",
      "source_application_id": "11111111-1111-4111-8111-111111111111",
      "source_module_key": "submission",
      "event_type": "documents.submitted.v1",
      "target_application_id": "22222222-2222-4222-8222-222222222222",
      "target_module_key": "records"
    },
    {
      "key": "result",
      "kind": "result",
      "source_application_id": "22222222-2222-4222-8222-222222222222",
      "source_module_key": "records",
      "event_type": "documents.processed.v1",
      "target_application_id": "11111111-1111-4111-8111-111111111111",
      "target_module_key": "submission"
    }
  ]
}
```

一个计划最多两个应用、八条连通且不重复的精确边；同应用不同模块合法，同一应用同一模块自连不合法。所有端点须属同企业、同环境，发起 Runtime 至少拥有一端；双方模块必须已经登记。事件能力可以在提案后继续开发，应用配置时双方须存活、启用且发布/订阅都已登记。`kind=forward/result` 描述方向，不是业务授权或处理器实现。

| Runtime 请求（须目标环境已声明支持并实测可用） | 作用 |
| --- | --- |
| `GET /api/v1/ecs-publisher/integration-plans/catalog` | 本企业同环境的非敏感应用、模块、事件目录及 Runtime 所属关系 |
| `POST /api/v1/ecs-publisher/integration-plans` | 提交上述精确计划，不批准、不自动创建路由 |
| `GET /api/v1/ecs-publisher/integration-plans?request_id=...` | 精确查原请求，返回数组，用于提交结果未知时核实 |
| `GET /api/v1/ecs-publisher/integration-plans/{id}` | 原 Runtime 查询状态、具体 gaps 及正常确认入口 |
| `POST /api/v1/ecs-publisher/integration-plans/{id}/apply` | `{ "version": "平台返回的64位版本" }`，仅应用当前获批精确计划 |
| `POST /api/v1/ecs-publisher/integration-plans/{id}/verification` | `{ "version": "平台版本", "delivery_ids": ["真实投递ID"] }`，读取保存的目标回执，不发起业务投递 |

`spec_digest` 和不透明 `version` 均由平台生成；客户端不能计算一个摘要冒充已批准版本。查询分别返回 `authorization_status`（pending/approved/rejected/revoked）、`configuration_status`（not_configured/configured/drifted/revoked）、`configuration_lease_expired`、`readiness.ready/gaps`、`transport_status` 与 `business_status`。configured 只表示配置已应用；business_acknowledged 只表示平台保存的目标业务回执有效。`verify` 返回后仍要验证源端最终状态和获权业务读回。

提案使用稳定 `request_id`：脚本先 GET 查同一请求，存在时只核对内容；提交结果未知时只 GET 查回，同 ID 内容不同即拒绝。apply 结果未知时只 GET 查询同一计划是否已配置；verify 未知时只查已保存回执。403/409 等明确拒绝不得自动换 ID、扩权或重新 POST；未知且读回仍不确定时保留 unknown，下一步用 status 核实。

目标处理成功的实际响应形状为：

```json
{
  "deliveryId": "实际收到的deliveryId",
  "eventId": "实际收到的eventId",
  "processed": true,
  "receipt": {
    "id": "稳定业务处理回执ID",
    "status": "completed",
    "entityType": "business_record",
    "entityId": "真实业务记录ID",
    "version": 1,
    "contentSha256": "可选：实际文件或规范业务内容的64位SHA256"
  }
}
```

`processed: true` 只能在对应业务事务确实完成后返回；业务失败或仅收件不得生成 completed 回执。平台复核匹配 deliveryId/eventId、端点和类型后保存回执，不从客户端上报一个 verified 标记。重复投递返回同一真实结果；文件型业务另在验收中对账内容摘要，不因摘要字段存在就认定内容正确。

## 验收

使用获授权测试数据/账号，从实际业务入口发起一次完整链路，并记录双方部署版本和真实结果；脚本不会为验收创建业务写入。

- 正常链：来源提交 → 真实平台 deliveryId → 目标 `processed: true` → 目标业务记录引用及版本 → 获权回读结果 → 来源展示相同最终结果。仅配置已应用仍是“待业务验收”。
- 重复与冲突：相同逻辑操作/事件再次到达只返回已有结果；相同 ID 不同内容拒绝；来源或目标已成功时恢复不得重复写入。
- 权限与撤销：无授权角色、错误企业/Runtime/模块/事件、停用/撤销/过期、确认前后目录或权限变化均拒绝；不能通过人工拼事件或复制凭证规避。
- 失败与未知：目标校验失败、超时、部分失败和返回 `processed: false` 时，不得显示成功；读回后只恢复未完成项，保留错误与关联标识。
- 文件和对象：校验实际文件摘要/版本、对象映射及目标内容，通用对象不能错归具体商品/人员；双端新增或变更页面分别验收，模拟器不冒充真机。

`integration_plan.py verify` 只读取平台真实投递记录并检查完成条件。它必须要求明确 deliveryId、`processed: true` 和业务记录引用，拒绝缺失、重复、其他计划/端点、失败或仅收件的结果；不接受命令行传入一个 `verified:true` 冒充平台证据。最终交接另附真实业务回读与双端结果，分别报告 SaaS/Skill/子系统的修改、提交、发布和验收状态。
