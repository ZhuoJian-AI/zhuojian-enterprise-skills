# 通用消息委托与通知业务边界

适用于本次新增或迁移的企业通知。普通子系统无需新增通知模块；既有系统不因 Skill 更新自动部署或改权。保持契约 2.4/2.5，不为可选能力改写接入版本。

## 归属与角色授权

子系统负责业务页面、本人草稿、模板、通知规则和业务记录。SaaS 负责当前员工身份、目录、逐 Action 数据范围、完整可信确认、通道投递和回执。企业差异通过子系统 Manifest 与配置声明，不写租户专用分支、员工名单或业务表单到 SaaS 公共前端；不向子系统发放钉钉密钥或平台数据库。

授权保留在企业管理员原有“角色权限 → 企业模块与页面 → 配置权限”。管理员给任意业务角色授权发送 Action 及其范围，再绑定员工；无需把员工提权成企业管理员，不依赖角色叫“主管”。多个角色只合并**实际授予这个发送 Action** 的范围，其他角色的全企业范围、可看页面或文件空间权限不能扩大收件人范围。子系统显示当前员工可操作的范围，不能自建另一套角色权限编辑器。

## 先确认平台实际支持

目标 SaaS 能力声明 `features.messageDelivery` 应含 `supported:true`、`version:1`、`authentication:"subsystem-sso-client-and-current-employee"`、`endpoint:"/api/v1/subsystem-sso/messages"`、`requiresConfirmedAction:true`、`mode:"immutable-preview-confirm-submit"`、`channels:["dingtalk"]`、`unknownOutcomeRetry:false`。核对目标发布版本与实际鉴权调用；旧 Runtime 未投影此能力、声明缺失或接口未部署时记录待验，不自行推断支持。Skill 更新不等于 SaaS 或 Runtime 已上线。

发送 Action 必须声明 `operation:"create"`、`messageDelivery:true`、`employeeDirectory:true`、`requiresConfirmation:true`，按既有规则登记页面与 `permissionPolicy`。声明是接入意图，不产生授权；网页与助手使用同一业务服务。保存本人私有草稿可用 create/update 且不逐次确认，边界及证据格式见 [写入与上下文](business-ai-delivery.md#写入与上下文)；发送始终确认。

## 最小接口

子系统后端向既有可信 SaaS origin 调用，使用原有 SSO 客户端 Bearer 凭据。每次传入从服务器 SSO/签名 Action 上下文取得的 `user_id,auth_epoch,module_key,page_key,action_key`；使用**发送 Action** 的上下文核收件人范围，不能让浏览器指定操作者。凭据不进浏览器、日志或 Skill。平台每次核对企业、应用、员工及当前 Action 授权。

以下路径相对于 `/api/v1/subsystem-sso/messages`，全部 POST：

| 路径 | 输入与结果 |
| --- | --- |
| `/recipients` | 上述上下文与可选 `query,department_id,offset,limit`；返回 `items` 的稳定 `user_id`、姓名/账号、部门及 `eligible/reason`，以及部门、分页和通道状态。不暴露钉钉 subject ID。 |
| `/preview` | `content,recipient_ids,business_reference`；平台冻结完整正文、发送人、具体名单与授权快照，返回 `id,delivery_digest` 和完整预览。`business_reference` 是子系统稳定业务单据编号。 |
| `/{id}/request-confirmation` | `delivery_digest,request_id,params`；params 包含相同 `delivery_id,delivery_digest` 及 Action 其他已登记参数。创建/复用平台 ActionRequest 待确认，不发送。 |
| `/{id}/submit` | `delivery_digest,request_id`；仅在平台可信确认后、签名发送 Action 执行时调用，request_id 沿用该 Action 的 requestId。平台返回投递回执，不接受子系统的 `confirmed:true`。 |
| `/{id}/status` | 当前上下文；查询同应用、同员工回执与 `confirmation_state`。业务历史留在子系统，保存平台回执引用。 |

preview 与 request-confirmation 是两个阶段。不要仅在子系统弹窗中设置 confirmed=true，也不要在创建草稿或请求确认时调用真实投递。

## 完整确认与执行

Action pending 的 `result.confirmation_kind="message_delivery"` 与 `result.confirmation_preview` 是平台可信展示数据，包含 `kind,delivery_id,delivery_digest,content,rendered_content,sender,recipients,total,expires_at`。必须让本人看完整正文、发送人和具体名单；截断摘要或只有人数不构成发送确认。确认 UI 放在 SaaS 通用确认入口；子系统通过已支持的任务/Action 确认入口交接，不能返回一个用户无法到达的 ID 冒充可用流程。

助手发起的请求标记 `result.confirmation_owner="assistant"` 与 `assistant_approval_id`，只在原任务确认。网页不得同时展示第二个手动发送入口；模型参数、工具批准或客户端伪造标记不能替代服务器保存的本人审批与执行 claim。钉钉确认卡绑定原消息、员工及企业身份；显示不了完整内容时引导到真实完整确认页，不悄悄缩短正文后发送。

平台保存确认绑定后才调用子系统签名 Action；子系统校验应用、企业、员工、Action、参数、requestId、确认与版本，再请求 submit。确认前及实际投递前重新核权；正文、名单、身份绑定或范围变化须重新预览。拒绝/过期回到草稿，旧确认不能重新发送。

同一请求重复调用只复用回执；同一企业/应用/员工/business_reference 已 queued、sending、completed、partial 或 unknown 时，不能换预览 ID 绕过去重。unknown 只核查回执，不自动重发，也不让 AI 生成新编号规避。accepted/已受理不等于送达或已读；平台与子系统都按真实状态显示。

## 验收

- 同一角色给不同范围、多个角色合并、无发送授权、跨企业/跨人/跨应用、停用/撤权/会话失效均按当前 Action 判断；未绑定通道员工显示具体原因。
- 网页电脑和手机、助手与钉钉使用相同完整预览；本人确认才有投递，拒绝/超时、参数变化、错员工确认及重复点击不产生第二次发送。
- 模拟通道超时、已提交但回包丢失、worker 中断，核查 unknown 不重发及 receipt 可查询。隔离测试不等于真实通道测试；真实发送须有已授权收件人与正文。
- 迁移前盘点历史、在途和旧授权，记录回退；没有历史数据不做空导出。有历史则保留可读/在途兼容，切断旧业务新建入口，不删除审计账本。
- 分别记录 SaaS 公共接口、子系统业务、Skill 契约的提交/部署/验收状态。其他企业与既有员工端按原路径回归，未测项明确保留。
