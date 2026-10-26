# 跨系统对接与受控配置

适用于同一家公司多个业务负责人使用的应用或模块协同、移动上传入口或共享办理结果。默认在同一台已初始化的企业服务器上复用已有应用、模块和权威业务服务；同一应用的不同模块也适用。服务器位置不决定对接方式，负责人不同不代表需要新应用、新 Runtime 或事件路由。多 Runtime/跨机保留兼容流程，不作为默认业务步骤。本流程保持既有 2.4/2.5，不要求无关子系统升级。

三个及以上应用/模块或“全部系统”的共同业务目标，必须同时按 [多系统对接与整条业务流程验收](multi-system-integration.md) 处理整体范围、实现拆分、已有关系复用、部分成功恢复与整链证据。负责人可在 Codex 一次确认完整业务清单；AI 自行实现企业服务及所需配置，只有选择平台事件的关系才逐个执行精确计划，无需逐项进入管理员前端。

## 先查真实链路，再分层实施

开发 AI 对完整结果负责：澄清业务结果和对象 → 查双方运行版本与已有能力 → 确定权威服务并选择最小对接方式 → 完成真实实现 → 在需要技术配置时取得精确确认并调用获权后端 → 验收双方真实业务结果。SaaS 负责统一身份、员工授权、通用助手和所选平台调用/事件的公共能力；企业子系统负责业务对象、文件、服务间委托、处理及结果，业务联通可全部落在企业服务器；Skill 负责选择、实施与验收流程。负责人确认业务目标、例外和重要影响，不替 AI 设计事件或准备平台令牌。

1. 先从已授权材料和真实页面确认：现在在哪里操作、希望最后得到什么、涉及哪类对象、谁能操作和查看、失败时怎样恢复。只追问缺失且影响结果的业务规则，按需使用随包“模块需求”，不重复已有答案、不让负责人选择技术方案。
2. 读取双方 Runtime/应用/模块身份和服务器当前源码，核对 Manifest、实际入口、API/Action、事件、业务服务与已有配置。不能只看服务器健康或本地旧副本；同机不等于共享数据库授权。
3. 明确权威业务记录归谁、另一侧保存草稿/附件还是只保留提交凭据。“只在目标系统保存”不能实现成两边各存一份再声称一致；必要的临时文件、传输队列与持久业务记录要区分。
4. 保留通用资料与按业务编号资料等真实对象边界，使用稳定 ID 和版本映射。文件名、同名对象或“目标已存在”都不能代替归属核对；不确定匹配要供人核对，不能取第一个候选。文件流程同时按 [资料识别与对象归属核对](business-identity-review.md)。
5. 优先复用目标既有解析、保存和查询服务；页面与助手调用同一业务规则。两套系统共享一个上传/解析/保存功能时，通常先保留一个权威实现，在另一侧接入口或受控调用；不因此复制业务记录、另建同类功能或合并两个完整应用。

| 实际需求 | 优先方式 | 是否需要本页事件计划 |
| --- | --- | --- |
| 进入已有页面、查看已存在的结果 | navigation Bridge、已有获权查询或页面复用 | 不需要 |
| 同一应用内多个模块复用规则/操作 | 同一业务服务，分别保持模块与动作权限 | 通常不需要 |
| 独立应用复用同一业务功能并立即取得结果 | 复用或由企业 AI 实现专用业务服务/API，配置真实调用身份；权威业务服务保存一次 | 不因跨应用自动需要 |
| 独立消费、异步处理或需排队重试 | 企业服务队列或版本化事件，真实消费者及结果查询/回执 | 仅选用平台投递时需要 |

同企业已获权开发的同步服务、原件交付与最终回读，先按 [企业服务器内业务服务对接](intra-enterprise-service-integration.md) 在企业项目实现并配置；没有现成接口是开发工作，不自动等于企业 AI 无权开发。核对旧项目 AGENTS，按当前业务授权修正“跨模块只能使用事件”等已不适用限制并保存 Git；不能仅更新 Skill 后保留旧架构阻断。现有集成计划 API 仅配置精确事件关系，不是任意跨应用 API 调用或业务角色授权。每条实际调用须有真实 Manifest/服务绑定、载荷与文件访问方式、可信操作者或明确机器委托、版本、幂等、失败和结果设计。不得直连另一业务数据库、共享应用密钥、以 Runtime/root 身份冒充员工，或虚构平台尚未实现的调用接口。使用平台事件时，来源必须声明 publishes、目标模块明确 subscribes，事件应带目标真正可处理的数据或受控文件引用。只有名称/版本的“已保存”摘要不能冒充可导入文件；不能复用用户临时下载链接、跨应用长期文件密钥或未获权对象来补数据通道；可由企业 AI 实现绑定精确文件/版本/目标/用途的专用文件委托，须有真实代码、配置及负例验证，不把它冒充已有 SaaS 文件接口。

## 业务处理和最终结果必须先做实

模板 `/api/integration/event-deliveries` 只提供验签、订阅校验、幂等收件和日志，默认返回 `accepted: true, processed: false`。它不会自动解析附件、创建业务记录或返回最终业务成功。开发 AI 必须接入目标真实服务，在业务写入、幂等结果和必要 outbox 之间保持一致；相同操作重放不得重复创建，ID 换内容须拒绝。

新版模板按“来源应用、事件ID、目标模块”识别一次逻辑消费，同一事件可由多个目标模块各自处理。路由变更产生新的deliveryId时，同一消费返回原业务结果并回显实际新deliveryId；不能再次写业务记录，也不能把另一个模块的结果当作本模块成功。旧全局UNIQUE(event_id)表的标准结构可保留记录升级；发现自定义列、索引、触发器或外部引用时，由AI备份后编写专项迁移，不丢弃扩展结构、不要求业务负责人修数据库。更新Skill不会自动更新已有消费者。

源端应区分待投递、已收件、已处理、失败及结果未知，并关联稳定提交标识、实际 deliveryId 与目标业务记录 ID/版本。目标要提供真实处理结果，源端采用既定受控回执事件或获权查询回读。平台 HTTP 200、`accepted`、事件日志存在或 AI 自称已完成都不能替代业务落库证据。长任务可以先收件，但在最终完成前不能展示导入成功；失败恢复先核对已成功结果，只重做未完成部分。

## 精确事件配置与 Codex 内确认

以下流程只用于前面选定的精确事件配置，不为普通页面复用或同步业务调用强加事件。先完成双方真实业务处理、Manifest发布/订阅与平台同步，再提出 `authorization_mode=runtime_endpoints` 计划。开发 AI 使用 `scripts/integration_plan.py` 读目录、提案、查询、确认/拒绝/撤销、应用和核对投递证据。凭证只由脚本在各自 Runtime 内部读取现有root所有、0600文件，不写入参数、计划、日志、仓库、交接或回复。

计划必须限定本企业的来源应用/模块、目标应用/模块、版本化事件类型和业务用途，不能带通配目标、任意 URL、角色变更、全局 Token 或数据库访问。原 Runtime 可以查询本企业目录并提出涉及自身应用的对接；跨 Runtime 的对端仍须完成已授权的代码与登记，不能据一个 Runtime 的服务器权限修改另一台服务器。

向负责人用业务话说明两端模块、数据/文件、唯一存储、允许操作、结果回流、影响和共同配置期限，取得对这个具体范围的明确确认；本对话已有相同范围的明确确认时复用，不重复追问。负责人可直接在 Codex 对话确认，不以登录管理员网页或运行浏览器自动化为必经步骤。聊天确认及CLI的 `--confirm-business-intent` 只是本地防误操作要求，不是SaaS人类身份凭据；真正权限来自已初始化Runtime及服务端当前端点归属，审计记录Runtime委托，不伪称某管理员已登录/批准，也不修改员工业务角色。

仅对接既有应用、没有新增或变更平台入口/界面时，用真实获权目录、当前登记、方案状态和业务结果验收，不为事件配置强制打开管理员前端；没有查看的页面不记为已验收。新增或修改业务页面仍须分别完成电脑和手机界面验收，API通过不替代页面结果。

默认两端属于同一企业 Runtime，由开发 AI 核对实际登记后在本机确认一次并应用；同一主机地址不自动合并 Runtime 身份。不让不同业务负责人分别运行技术命令或重复确认同一业务范围。Runtime 是企业应用的部署身份，不是负责人个人身份；此配置委托不会改变负责人或员工的业务角色、模块与 Action 权限。

只有现有应用实际分属多个 Runtime 时，开发 AI 才分别通过已有获权连接，用各端本机 key 确认同一个公开 `authorization_digest`，不汇集 key、不把一个 Runtime 权限扩展到对端，也不让负责人处理机器 quorum。支持self-service能力的平台由`discover`分页查当前归属参与计划；旧列表和request_id查找仍归原申请者。计划ID与公开摘要可以交给对端，摘要不是密钥。所有参与Runtime有效确认齐全后，仅原申请Runtime可以apply。

新模式的 `configuration_ttl_hours` 为1至168的整数，省略时72小时；平台在提案时固定所有参与者共同的绝对 `apply_expires_at`。后签不延时，确认不会重设期限。公开授权摘要绑定精确方案、企业/环境、双方owner、模块/事件契约与该期限；不等于不透明 `version`，他端对同一范围确认使version变化时摘要仍可保持。相关归属、凭据或契约漂移后须新计划，不能自动改签旧确认。

支持`contractProjectionRevision=2`的平台只比较本关系相关的发布/订阅契约；增加第三个系统使用的不相关事件，不应中断已有关系。平台可在旧契约仍精确有效、替换Manifest之前保存兼容证明，保留旧授权摘要与原确认。已在升级前漂移且没有该证明的旧计划不能倒推出原契约或补造同意，须由AI核对业务结果并按实际差异处理；不通过改旧hash、换事件ID或新计划绕过历史范围。

未齐确认、已拒绝/撤销、共同期限届满或能力漂移时不应用；不索要主平台root/管理员Token，不自行扩大Runtime登记或直写数据库。配置期限只限制何时apply，已经建立的业务关系持续至明确撤销。中断或未知结果先读同一计划；confirm必须核对本Runtime的 `confirmed=true` 且 `valid=true`，不能把别人确认或全局approved当作本端已确认。没有确定结果就保持unknown并交接，不自动重新POST。

旧 `authorization_mode=administrator` 仍是兼容模式，保留管理员会话入口；旧计划不会因新版CLI原地变成Runtime委托。旧平台或缺新委托能力时明确报告具体缺口，继续已授权准备；不假设API已部署，不偷偷调用管理员接口或要求业务负责人准备Token。

合法企业管理员也可通过既有后台自愿批准新模式计划，作为独立的较高授权，不要求再凑齐机器确认。此时Read明确 `authorization_authority=enterprise_administrator`，不冒称Runtime quorum已齐，CLI不再POST确认、由原申请Runtime按当前version应用。管理员只能保留或收窄原共同deadline；若平台因此重新生成授权摘要，旧摘要和机器确认不能冒用。该入口可选，不是Codex流程的前置条件。

先判断缺失能力是否是所选路径的必要依赖。企业服务器内专用服务不以平台事件、平台跨应用文件或任意特性字段为默认前置；开发 AI 在已有服务器授权内继续实现、配置、部署和验收该路径。只有已选择且不可替代的平台能力缺失、真实端点不在已有授权内，或业务范围尚待确认时，才阻断对应步骤；继续其余已获授权的开发、测试和交付，在各项目 `docs/ai-delivery.json` 及脱敏交接列出：确切缺口、责任层、已完成部分、计划标识/状态、所需本机Runtime及业务确认、验收条件和恢复下一步。未获权操作保持待执行，不泛称“找平台方开通”后结束全部工作。平台待办按 [业务提效设计与交付](business-ai-delivery.md) 提交，未提交不能称已受理。

## 平台接口与 Runtime 命令

脚本每轮先做一次获权 `platform-capabilities` 发现。基础操作须声明 `features.integrationPlans.supported=true/version=1`；新模式还须声明 `features.integrationPlanRuntimeAuthorization` 的supported=true、version=1、authorizationMode=runtime_endpoints、authority=runtime-owned-app-configuration、allParticipantRuntimesRequired=true、requiresAdministratorSession=false。目标接口须真实可用，返回的任意URL不作为脚本可执行目标。旧能力 `integrationPlans.requiresEnterpriseAdministratorApproval=true` 仅描述兼容管理员模式，不能据它否认新委托支持或要求新模式再找管理员；按实际所选 `authorizationMode` 核权。顶层 `requiresCurrentEmployeeAuthorization` 描述员工业务调用，不能读成所有 Runtime 技术配置均需员工登录。Skill发布不证明SaaS已经部署。

### 能力漏报与本机 Runtime 更新

`zhuojian-runtime platform-capabilities` 是本机 Runtime 对 SaaS 响应的安全投影；旧投影可能过滤新增字段。字段缺失先记为待核实，不直接宣称平台没有实现。需要事件时，可在同一 Runtime 用本 Skill 的 `integration_plan.py catalog` 只读核对；该脚本使用档案中的固定平台地址和本机登记凭据，直接检查 SaaS 能力。记录查询时间、环境、本机脚本版本及脱敏能力字段；不要输出凭据、原始失败正文或把 key 带回开发电脑。

若直接能力检查支持而 CLI 漏报，核对已安装 `runtime_admin.py` 与当前稳定 Skill 的 Runtime 资产，按 [Runtime 安装与维护](admin-bootstrap.md#runtime-维护与能力投影) 修复本机投影并复查。保留当前配置、登记凭据、应用和备份，更新 Runtime 不重新初始化企业，也不等于业务服务已部署。若 SaaS 真实响应确实缺失必要能力，仅对应平台路径受阻；可在当前授权内实现的企业服务路径继续推进。

提案、列表/request_id查找、apply和verification在原申请Runtime运行；参与端按计划ID查询保存的状态/回执，并在各自本机confirm/reject/revoke，不复制登记key到开发电脑、其他Runtime或命令参数。默认读取 `/etc/zhuojian/runtime.json` 中的 `platform.baseUrl` 与 `deployment.registrationCredentialRef`；文件引用由Runtime提供。平台origin必须HTTPS，脚本不跟随重定向、不输出失败响应正文。

Skill 只在开发电脑时，由开发 AI 通过既有获权 SSH 将 `scripts/integration_plan.py` 和脱敏计划复制到该 Runtime 的任务临时目录并用其 Python 3 执行，或使用等效已验证的远程脚本方式。不要为执行助手脚本把 Runtime key 取回本机、给员工安装开发 Skill，或放宽凭证文件权限；这也不要求修改 Runtime 可执行程序。

```text
python <skill>/scripts/integration_plan.py catalog
python <skill>/scripts/integration_plan.py discover --limit 50
python <skill>/scripts/integration_plan.py routes --source-application-id <来源应用UUID> --target-application-id <目标应用UUID>
python <skill>/scripts/integration_plan.py propose --plan <本地脱敏计划.json>
python <skill>/scripts/integration_plan.py status --request-id <稳定请求标识>
python <skill>/scripts/integration_plan.py status --plan-id <平台返回的计划ID>
python <skill>/scripts/integration_plan.py confirm --plan-id <计划ID> --authorization-digest <已审查的公开摘要> --confirm-business-intent
python <skill>/scripts/integration_plan.py apply --plan-id <计划ID>
python <skill>/scripts/integration_plan.py verify --plan-id <计划ID> --delivery-id <真实投递ID>
python <skill>/scripts/integration_plan.py revoke --plan-id <计划ID> --authorization-digest <公开摘要> --confirm-business-intent --reason <撤销原因>
```

需要指定受保护Runtime档案时，将 `--runtime-profile <档案>` 放在子命令前；不能绕过身份绑定。`confirm/reject/revoke` 必须显式提供所确认计划的 `--authorization-digest` 及本地业务确认参数，body只传摘要、拒绝/撤销可附reason，不传伪造人类身份或confirmed标志。`apply/verify` 用另一种不透明 `--version`，省略时先读当前version。脚本不执行验收业务写入，不改业务角色；新模式不要求approval_url。`reject` 参数与revoke相同，只拒绝待确认计划。

计划 JSON 只包含以下字段；应用 ID、模块键和事件名从真实获权目录与双方代码确认，不照抄示例 ID：

```json
{
  "request_id": "document-transfer-20261024-01",
  "title": "提交资料并返回处理结果",
  "purpose": "从提交模块送至记录所有方处理，并显示真实结果",
  "data_description": "版本化结构化字段及获权文件引用；不含密钥或原始业务数据",
  "ownership_description": "目标拥有业务记录，来源只保留提交和最终结果引用",
  "authorization_mode": "runtime_endpoints",
  "configuration_ttl_hours": 72,
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

一个计划最多两个应用、八条连通且不重复的精确边；同应用不同模块合法，同一应用同一模块自连不合法。端点须属同企业同环境，申请Runtime至少拥有一端；新模式先开发并同步双方模块、发布/订阅能力后再propose，提案时冻结契约。兼容管理员模式可在提案后继续补能力，但不能apply未就绪关系。`kind=forward/result` 不是业务权限或处理器实现；数组排列不定义执行顺序，按稳定edge key规范化比较同一图。

| Runtime 请求（须目标环境已声明支持并实测可用） | 作用 |
| --- | --- |
| `GET /api/v1/ecs-publisher/integration-plans/catalog` | 本企业同环境的非敏感应用、模块、事件目录及 Runtime 所属关系 |
| `GET /api/v1/ecs-publisher/integration-plans/discovery?limit=50&cursor=...` | 当前Runtime归属的参与计划分页，非仅本人最近100项；可按application_id筛选 |
| `GET /api/v1/ecs-publisher/integration-plans/routes?source_application_id=...&limit=50` | 本Runtime同时拥有两端的既有路由、接管条件和阻点；可按target_application_id及cursor筛选 |
| `POST /api/v1/ecs-publisher/integration-plans` | 提交上述精确计划，不批准、不自动创建路由 |
| `GET /api/v1/ecs-publisher/integration-plans?request_id=...` | 精确查原请求，返回数组，用于提交结果未知时核实 |
| `GET /api/v1/ecs-publisher/integration-plans/{id}` | 新模式当前参与Runtime按ID查看精确范围、共同期限、各端确认与gaps；兼容旧模式仍原申请者 |
| `POST /api/v1/ecs-publisher/integration-plans/{id}/confirm` | 新模式，`{ "authorization_digest": "精确公开摘要" }`，只确认当前Runtime拥有的端点 |
| `POST /api/v1/ecs-publisher/integration-plans/{id}/reject` 或 `/revoke` | 新模式，同摘要，可附 `reason`，不接受version或客户端confirmed标志 |
| `POST /api/v1/ecs-publisher/integration-plans/{id}/apply` | `{ "version": "平台返回的64位版本" }`，仅应用当前获批精确计划 |
| `POST /api/v1/ecs-publisher/integration-plans/{id}/verification` | `{ "version": "平台版本", "delivery_ids": ["真实投递ID"] }`，读取保存的目标回执，不发起业务投递 |

摘要及version均由平台生成，客户端不能自造。新模式Read提供 `authorization_mode`、`authorization_digest`、`configuration_ttl_hours`、`authorization_authority=runtime_app_owners`、`requires_administrator_session=false`、`runtime_confirmations` 和当前Runtime ID/application IDs/can_confirm；它们描述机器委托与当前归属，不是人类身份认证。状态另含authorization_status、configuration_status、configuration_lease_expired、readiness、transport_status及business_status。configured只表示配置已应用；business_acknowledged只表示保存的目标业务回执有效，仍要源/目标实际读回。

提案使用稳定 `request_id`：脚本先 GET 查同一请求，存在时只核对内容；提交结果未知时只 GET 查回，同 ID 内容不同即拒绝。apply 结果未知时只 GET 查询同一计划是否已配置；verify 未知时只查已保存回执。403/409 等明确拒绝不得自动换 ID、扩权或重新 POST；未知且读回仍不确定时保留 unknown，下一步用 status 核实。

## 既有关系、遗漏投递与后续AI接手

先核`features.integrationPlanSelfService`的supported=true、version=1、contractProjectionRevision=2、recoveryScope=original-plan-event-window及requiresAdministratorSession=false。`discover`与`routes`返回`items/has_more/next_cursor`；AI持续按next_cursor读到has_more=false，记录范围、应用筛选和已读游标，不能把一页或旧列表当全部关系。查询只覆盖当前Runtime获权参与范围，目录不完整时明确缺项。

已生效且端点、事件及业务用途匹配的计划优先复用。接管手工旧路由还须声明`exactActiveRouteAdoption=true`，先用`routes`核adoptable/blockers，再把精确`adopt_route_id`写入对应edge、纳入整体业务确认与计划摘要；AI不需进入管理前端找ID。仅本Runtime同时拥有两端、精确active且未删除、未托管、旧队列已结清的关系可原地接管，保留原routeId及已完成投递。通配、禁用、软删或尚有pending/delivering/failed的手工关系先核具体影响，不静默覆盖。原托管计划已撤销后，重新业务确认的新计划可按平台明确支持的规则建立新关系，旧授权、旧队列和审计不复活。

需要恢复投递时，AI先核目标真实结果和幂等实现。`recovery-list`只列原计划configured_at之后且source_sequence高于原floor的事件，不返回业务正文，不自动重放。新计划不能越过自己的floor补跑旧历史；必须留在仍有效的原计划范围，或另行完成明确获权的业务对账/补偿实现。

```text
python <skill>/scripts/integration_plan.py recovery-list --plan-id <原计划ID> --edge-key <精确关系键> --limit 50
python <skill>/scripts/integration_plan.py recover --plan-id <原计划ID> --request <脱敏恢复请求.json> --confirm-business-intent
python <skill>/scripts/integration_plan.py recovery-status --plan-id <原计划ID> --request-id <同一恢复请求ID>
```

恢复JSON固定为`{version, request_id, reason, items:[{edge_key,event_id}]}`，1至100个不重复精确项。request_id使用稳定英数、点、冒号、下划线或连字符，正文写已确认恢复原因，不含原业务载荷。负责人已确认包含故障恢复的整体范围时直接复用，AI自行逐批拆分，不逐事件询问。服务端整批核权，拒绝在途/未知任务；已完成项沿用原delivery，失败项才恢复待投递。CLI先GET同一request，再校验当前version；回执核请求摘要，写请求未知只GET同ID，保留unknown，不自动重POST或换ID。`recovery-status`是请求受理回执，delivery状态可能已变化，应另读最新候选与真实目标结果。

接口为`GET/POST /integration-plans/{id}/recovery`及`GET /integration-plans/{id}/recovery/requests/{request_id}`，均在固定`/api/v1/ecs-publisher`下，使用当前参与Runtime本机身份。恢复返回`business_completed:false`；排入队列或拿到回执均须继续实际业务读回和整链验收。上述能力未部署时如实列出缺口，继续其他获权工作，不要求负责人手工创建路由或索要平台Token。

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
