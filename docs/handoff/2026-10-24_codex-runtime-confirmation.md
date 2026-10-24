# Codex 内确认精确事件配置（core1.1.43候选）

本次按用户要求补齐“仅Codex＋已初始化企业应用服务器”的配置流程，不要求负责人进入管理员前端。SaaS负责Runtime端点归属、共同授权摘要/期限、机器委托与审计；Skill负责先澄清并复用业务、展示精确影响、各机执行CLI和真实业务验收。聊天同意及本地显式参数不是平台人类身份凭据，不把Runtime确认写成管理员登录。

## 业务与授权边界

先确认对象、最终结果和唯一存储，再复用既有权威服务。页面导航/查询、同应用共享服务、获权同步API/Action、异步事件分别选择；独立系统共享功能不代表需要合并整套系统、重复存储或新增事件。当前新API只授权精确事件技术配置，不开放任意跨应用API或员工业务角色。

默认业务流程显式提出 `authorization_mode=runtime_endpoints`。先完成双方真实处理与发布/订阅同步，再propose；平台固定 `configuration_ttl_hours`（默认72，1至168整数）、共同绝对deadline和公开authorization_digest。跨Runtime各机使用本机root-owned0600登记key确认同一摘要，不汇集key；同Runtime两端只确认一次。所有参与方有效确认齐全后，仅requester apply/verification，参与方可按ID GET保存的状态和回执。

合法管理员可选择独立批准新模式，Read明确enterprise_administrator授权，原申请者无需再凑机器quorum即可apply；管理员不是Codex流程必经入口。旧administrator模式与旧请求spec保持兼容，不能自动转换；新委托能力未发布时报告精确capability gap，继续已授权准备，不索要平台root/Token。

## CLI

- 新增confirm/reject/revoke：固定路径，显式 `--authorization-digest` 与 `--confirm-business-intent`，body不接受伪造human identity/confirmed标记。后两项可附reason。
- 公开authorization_digest与opaque version分离；他端对同范围确认改变version不影响摘要，共同deadline不延时。同request_id改变TTL会被精确比对拒绝。
- confirm未知先GET同计划，必须看到本Runtime对应的confirmed且valid，不拿他端确认或全局approved充当本端成功。拒绝/撤销未知只核同摘要/当前参与方的终态，不重发POST。
- 端点迁移后当前新owner仍可撤销旧关系，不要求先签署旧snapshot；不再拥有任何端点的原申请方不能代决定。没有扩大Runtime登记、主机或业务权限。
- 保留HTTPS固定origin、无重定向、凭证仅本机读取、脱敏错误与字段白名单；展示业务说明、精确边、共同期限、当前端点和确认状态。真实business receipt不等于源端已回读。

## 范围与验证状态

修改核心SKILL、跨系统/聚合/初始化/平台契约参考、CLI、受影响版本测试和新机器确认测试，候选版本1.1.43；保持2.4/2.5、模板、Manifest Schema、其他Skill及发布工作流不变。

本机Windows任务Python3.13已实际运行26项标准库unittest、CLI帮助和编译检查：通过。覆盖双独立传输身份/逐端确认/原申请者apply、同机双端、精确TTL与摘要、缺本地确认零请求、权限/409不重试、未知及不完整响应GET核实、错误全局approved、当前新owner撤销、可选真实Admin授权、脱敏输出。均为无网络的合约fixture，不接生产。

完整core pytest、quick_validate及正式PR CI待补实际结果；尚未发布Release、更新个人安装或部署SaaS/Runtime/业务应用。业务页面、业务数据、真实跨系统投递与负责人业务授权不由Skill源码提交自动完成。
