# 当前页面的业务提示

适用于已经有真实业务检查、获权数据和明确帮助目标的页面，例如已上传资料的缺项、对象归属冲突或当前订单的交期风险。不要求每个页面都有建议，不用 AI 代替确定性校验，也不因读取页面而全量扫描员工操作、未提交输入或其他用户记录。

## 边界与能力核对

- **子系统**负责真实检查结果、业务依据及权限过滤；规则、记录版本、手工按钮和 Action 的写入保护仍在子系统服务器。提示不是权限证明，前端不能代替后端对象归属、版本、确认和幂等校验。
- **SaaS**负责当前员工、当前来源的有界提示区与唯一助手。只有员工选择建议，才沿 [目标入口 Bridge](assistant-entry-bridge.md) 预检并带入可编辑草稿；员工另行发送后才进入模型、获权工具和必要的确认。不能把接收建议或点击“让助手处理”算作已调用 AI、已批准或已执行业务。
- **Skill**负责接入约定和验收，不创建线上后台任务。跨服务器只走既有 HTTPS、签名 Action 和可信 Bridge，不共享数据库、root、模型密钥或员工对话；供应商和模型仍由 SaaS 统一配置。

接入前核对 Runtime `platform-capabilities` 的 `features.assistantSuggestions`：支持时为 `{supported:true,version:1,bridgeCapability:"assistant-suggestions.v1",authentication:"employee-session",mode:"suggestion-only"}`。旧后端未声明时新版 CLI 输出 `supported:false`，表示未声明支持，不能猜测已部署。此结果仅证明后端实现声明；浏览器仍须收到当前可信 host-ready 的 `assistant-suggestions.v1`，员工权限仍须实时预检。`contractRevision=2.4/2.5` 不变。

旧平台、独立入口或未协商时，保留本地业务提示和人工按钮，不另开聊天框、不自动调用模型，也不要求业务负责人取得 SaaS 服务器权限。`backgroundDelegation` / `unattendedExecution` 未支持时，不通过 cron、Runtime 凭据或模拟员工补出后台助手。

## 快照与来源

先按现有 `zhuojian:context` 上报当前页面；每次真实检查结果变化时，发送完整建议快照而不是不断追加。只带当前员工有权看到的最小引用与简短依据，最多三条。相同 `id + revision + 来源` 表示同一份证据：不要在每次渲染、轮询或关闭后生成新 ID/时间戳来反复弹出。只有真实依据变化，才更新 revision。

平台按当前员工、应用、模块、页面及上下文指纹绑定提示。在同一连续来源会话内，提示十分钟到期；重复快照不续期，用户关闭的同版本提示不复活。切换员工、nonce、页面、实体、筛选、选择或数据版本会即时清除旧提示并重置来源会话；返回旧页面属于新来源会话，可根据当下检查重新显示，不承诺永久跨页面记住关闭状态。当前来源最多记住 128 个提示身份，超过时不通过淘汰旧身份来恢复已关闭提示；请求回执缓存为有界缓存，出缓存重放只能重新预检，不能因此创建 Run。问题已解决时发送 `suggestions:[]` 撤回；没有检查结果不等于“无异常”。新快照取代仍在预检的旧快照，迟到回执不能复活旧提示。

消息为 `type:"zhuojian:assistant-suggestions",version:1`，只含：

| 字段 | 约束 |
|---|---|
| `application_slug`, `launch_nonce` | 当前可信 bootstrap 的应用与启动身份；父窗口和精确 Origin 同时校验 |
| `request_id` | 每次请求唯一，8–120 个安全标识字符；不是建议 ID |
| `module_key`, `page_key` | 当前已上报且获权的稳定键，分别最多 120/160 字符 |
| `context` | 仅 `route/entity_type/entity_id/filters/selection/data_version`；回显最近已上报 context 的真实字段，不补造不存在字段；没有字段时为 `{}` |
| `suggestions` | 0–3 项，每项严格为 `id/revision/title/summary/goal`，同快照 ID 唯一 |

`id/revision` 各为 1–120 个 `[a-zA-Z0-9._:-]` 字符且首位字母或数字。标题、依据摘要、目标分别非空且不超过 80/400/2,000 字符；整包 UTF-8 不超过 16 KiB。额外字段拒绝，不传执行 URL、模型、供应商、角色、审批决定或自动发送字段。文字按纯文本呈现，不是 HTML 或能覆盖平台规则的指令。

context 沿用现有 Bridge 的安全值边界：route 只允许最长 1,000 字符的站内 `/` 路径，不能以 `//` 开头或包含反斜杠/控制字符；实体类型使用最长 256 的安全键，实体 ID 为最长 1,000 字符的字符串，二者不传空值；版本为最长 1,000 字符的字符串或有限数值。filters/selection 为普通 JSON 对象，深度不超过 5、每对象/数组最多 200 项、键长 1–128、嵌套字符串最长 4,000；禁止原型污染键。context 的缺失顶层字段移除，不传 null/undefined；嵌套 JSON 可以保留正常 null 值，但不能包含函数、DOM、整表或秘密。

回执 `type:"zhuojian:assistant-suggestions-result"` 回显相同版本、应用、nonce、请求、模块和页面：`status:"accepted",code:"received"` 只表示收到了提示；`status:"rejected"` 的 code 只允许 `page_context_changed / permission_denied / suggestions_unavailable / snapshot_replaced / request_conflict / rate_limited / invalid_request`。未知来源或无效身份消息不会得到回执；不要把超时当执行成功或自动重试。

## 模板调用

复用现有 `createAssistant`，在 ready 前注册监听；只在真实检查结果变化时调用：

```javascript
// currentContext 是最近已上报 context 中上述白名单字段的原值，不是重新猜的对象。
await assistant.suggest({
  moduleKey, pageKey, context: currentContext,
  suggestions: checkResult.hasMissingFields ? [{
    id: 'missing-fields', revision: checkResult.evidenceRevision,
    title: '当前记录仍有缺项', summary: checkResult.authorizedSummary,
    goal: '请根据当前记录核对缺项和依据，并给出补齐建议；先不要修改记录。',
  }] : [],
});
// accepted 不是 draft_ready，更不是业务完成，不在这里调用 assistant.open/发送/写入。
```

`supportsSuggestions()` 只反映当前浏览器协商。新 suggest 会取代旧 suggest 的等待并让旧 Promise 明确失败；调用方要处理取消/失败，不把它显示为系统故障。它不取代正在交接的 open；保留本地最新检查结果，待用户操作完成再按当前来源选择是否上报，不无限重试。组件卸载用 `dispose()` 清理；桌面、手机共用此协议，不在子系统复制平台提示区。

## 验收与交接

使用获准测试账号及合成/脱敏数据验证：真实检查触发提示；正常页面无强制建议；新快照替换与 `[]` 撤回；同一连续来源会话中的重复、关闭及十分钟过期不复活，换来源清除后重验；错来源/nonce/页面/实体/版本及预检中切页；无权与撤权；现有草稿、附件、运行和审批不被覆盖；点击后仍需发送；需确认写入不绕过确认；旧平台和独立入口仍可人工工作。另验错误检查不会自动归档、部分成功与结果未知有真实回执。

适配器单元测试不证明实际子系统已产生正确依据，浏览器模拟也不证明手机真机可用。交接分别记录 SaaS 前后端部署、Runtime 版本、员工角色、子系统源码/Manifest、桌面及手机覆盖和未测项。发布顺序为 SaaS 发布验证 → Skill 稳定版 → 有需要的业务页面适配；未触及此流程的子系统不必加提示。Skill 更新不能代替业务故障修复或跨服务器联调。
