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

本机Windows任务Python3.13已实际运行27项标准库unittest、CLI帮助和编译检查：通过。覆盖真实CLI解析、双独立传输身份/逐端确认/原申请者apply、同机双端、精确TTL与摘要、缺本地确认零请求、权限/409不重试、未知及不完整响应GET核实、错误全局approved、当前新owner撤销、可选真实Admin授权、脱敏输出。均为无网络的合约fixture，不接生产。

冻结Skill源码 `d3351c58d8e33f9bfc3e114f2a5a12c34a2bb3bd` 的完整core在公司CI任务独占容器、无网络/端口/生产挂载条件下实际运行：**709 passed、58 skipped、1既有Starlette/AnyIO弃用warning，17.45秒**；quick_validate通过。58项跳过为原始模板路径或缺Node/Playwright的环境项，不计作通过，正式Windows PR工作流另按实际报告。core tree为 `502d9da0c1761884317492af005acf1ece64412e`；此后仅补本交接/TASKS，不改变已测试核心字节。

初轮复用后端测试镜像缺正式gateway/template依赖，生成模板子测试未结束即停止，保留partial/exit137；补齐正式requirements后全量结束，仅两个旧OSS fixture因默认umask022生成0644文件，被原root0600检查正确拒绝。最后仅将任务容器进程umask设为更严格077重跑同冻结源码通过，没有修改fixture、loader或断言，没有调用真实OSS。日志和镜像ID在本机 `audit-2026-10-24/codex-runtime-confirmation-skills/accepted-report.json`；原环境失败记录保留。

独立联合验收使用实际Skill CLI main/urllib client与SaaS `142830c5866e9635239c5281992e134a1e8783da` 的真实ASGI路由、隔离PostgreSQL：11条命令/24次调用通过，包括提案、source确认DB提交后模拟响应丢失→只GET核实无重复POST、peer确认、requester应用、peer撤销，以及后续目标模块删除后当前owner仍可GET/撤销、dispatch零业务HTTP。测试适配器仅将真实urllib请求转接ASGI，不是实际TLS/SSH或生产企业端到端。脚本Git blob `b59f117bb0944a55b0650ebb698c97f4bf28a822`，原字节SHA256 `14b246db3fcf4d1eadd639e34df7024c393eb79776e21a30db18f31fbeed53ac`；联合证据为本机 `audit-2026-10-24/codex-runtime-integration/142830c-joint-client-api-proof.json`，SHA256 `4aa23b482cc175f1a58c9d1ca94452f2a87f8555919af171d61cf0364db04dd3`。

正式PR CI与合并尚待完成；尚未发布Release、更新个人安装或部署SaaS/Runtime/业务应用。业务页面、业务数据、真实跨系统投递与负责人业务授权不由Skill源码提交自动完成。
