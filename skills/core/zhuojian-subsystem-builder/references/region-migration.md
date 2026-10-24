# 已接入 Runtime 的跨主机与跨地域迁移

适用于管理员已授权的换机、地域、IP 或 OSS 迁移。企业专属地址和通道放在匹配的交接 Skill；通用 Skill 不设置默认企业或地域。ECS 与轻量应用服务器可以混用，实际网络、容量和持续负载须验证；“同地域”不等于自动内网互通。

## 身份与责任

- SaaS 负责平台数据库、统一登录/权限、Runtime 登记、网关、签名、回调和公共入口；子系统负责自身数据库、文件引用、同步任务与企业内网通道；Skill 负责接入契约、选址记录和验收交接。
- 从源和目标 `/etc/zhuojian/runtime.json` 读取已验证的企业、组织、Runtime与域名后缀及应用登记。空白目标换机沿用源Runtime；目标已有初始化Runtime时按下节做同企业归并，保留目标档案和原应用身份，不用源profile覆盖它。不得根据公司展示名重建企业，或因旧地域缩写改名。
- 源端、隔离目标和已接管目标分别记录。在接管前阻止目标副本自动登记、发布回调、业务写入、同步/备份/清理任务；复制了配置不等于可以同时启动全部服务。两个路径均保留原应用/release UUID、slug、模块/Action、角色、数据库主键、应用凭据及文件键。

## 同企业归并到已有Runtime

这是保留既有系统的主机归并，不是新建应用或重做业务。先比对源/目标组织与environment、原app/release UUID、健康commit、Manifest/模块/Action/角色摘要、数据/文件和目标非目标应用基线。目标默认Runtime档案、登记key、现有应用目录、端口、网络、代理与证书保持；不能整目录覆盖`/etc/zhuojian`、运行ensure-app重建旧应用或切换默认profile假装多Runtime。

先完成隔离候选、真实域名/TLS和依赖验证、一致备份/初副本，再在最终停写窗口完成增量与校验，按实际授权正常停用源Runtime。源停用会影响该Runtime全部应用及未消费SSO code，应在其全部迁移项目就绪后串行接管，不让目标候选抢先登记或双写。

保留原域名与登记时，先用目标Runtime实际查询SaaS能力`features.registeredApplicationOriginRegistration` v1，并GET其`lookupEndpoint`返回的原模块。只接受同组织、同environment的已停用源Runtime、原健康release及相同受管app；SaaS同时核`release.base_url`与未删除app的`entry_url`，拒绝任意alias、客户端metadata或不同app。请求和两个既有origin均为HTTPS root URL，scheme/host/port一致，无用户信息、非root路径、query或fragment；尾根斜杠按真实接口规范化。能力缺失时继续复制/核验等独立工作，不能自行放宽域名或改平台登记。

新版受管helper安装与其原字节、doctor验证后，在目标调用：

```text
zhuojian-runtime adopt-origin <原slug> --application-id <原appUUID> --source-runtime-id <真实源RuntimeUUID> --base-url <原HTTPS入口> --commit <原健康commit>
```

`adopt-origin`只保存逐应用root0600的`/etc/zhuojian/origin-adoptions/<slug>.json`，绑定平台实际app/org/来源与requester UUID、environment、原origin和首健康commit；它不启动容器、改SaaS、复制profile或生成新凭据。`runtime.json.runtimeId`是档案key，不能当UUID；实际requester来自新GET只读字段`requester_runtime_id`，`runtime_id`仍是release当前owner，`owned_by_requester`用来区分首次接管和目标日常更新。

首次跨owner只以原健康commit、原应用凭据与旧入口执行真实登记，不先对别人release执行begin-change；发布SDK显式传`--application-slug <原slug>`，继续校本机Git/运行容器/image/Secret及平台记录。成功或结果未知后GET同一slug，核原app/release ID和`runtime_id==requester_runtime_id`；未知不自动重复写入。已属目标后按普通begin-change/回滚/重试流程维护旧origin，记录不授权任意URL或员工权限。发现/同步失败可能保存目标owner和failed状态，不能假定整事务回滚或新建同名应用。

既有应用保持原持久授权策略。`initial_access_policy=disabled` 可用于新建时关闭授权，或原策略已经disabled的既有应用，不能当作“保留既有权限”的通用开关；既有非disabled应用传它会被拒绝。重登前核原Manifest、开发者受管grant和业务角色，重登后比对原Action/grant/角色/四凭据及非部署身份配置；不能为通过迁移而重授权限或改业务声明。源码、HTTP Manifest和SDK语义预检与真实POST分别记录。

中断后先只读核实已完成阶段及仍运行的进程、配置和定时任务，保留原intent与失败记录。需要续程时新建仅处理剩余步骤的受审入口，绑定真实前置状态和旧失败摘要；不能删除失败文件、重跑整套停写或伪造成功回执。下游复制、导入和转发也须识别该已审续程的实际完成证明，不能用泛化的“忽略失败”解除检查。

local-managed的数据、文件、原Secret、库路径和稳定键随一致性点迁移；目标有OSS也不改变原模式。接管后执行并核实`zhuojian-runtime backup-all`涵盖既有与迁入的全部受管应用、实际归档摘要和恢复路径，不只检查采用应用或命令退出码；按现有备份行为验证服务恢复，不声称零中断。候选复制、helper安装、平台归属、DNS、单活任务、完整备份与用户验收分别记录；源业务已停止后可进入观察保留，所有承诺项完成后才报告迁移全部验收通过。

备份生成、只读导出、异机下载校验、ACK和恢复演练分开验收。它们的任一安装或登记成功不能代替下一步；整批容量门禁影响哪些应用必须明确记录，未验证恢复则保留独立待办。源业务已停用观察与迁移全部验收完成也应分开表述，保留源数据和历史，不因主机归并删除旧资源。

## 盘点、复制与验证

1. 记录源/目标实例、IP、架构、系统、磁盘/挂载、余量、镜像 digest、真实运行 SHA、数据库与外部依赖。检查 root-only 凭证文件存在、权限和可用性，不回显内容。源端 `.git`、Runtime release、网关身份库、Docker 私网、代理、证书和受限隧道属于运行依赖，不只复制业务仓库。
2. 审查 DNS 的精确记录和通配符、TLS、IP 白名单、OAuth/SSO、CORS/iframe origin、Webhook、Registry、备份目标和定时任务。域名原则上保留，IP 变化只更新真正绑定 IP 的配置；不对源码/数据库进行全局字符串替换。
3. 保持源服务，先做完整复制；数据库使用该引擎的一致性备份/恢复，不复制运行中的数据目录冒充备份。业务文件和数据库引用形成同一可恢复点。目标公开前用本地 hosts 或浏览器域名解析覆盖验证真实域名/TLS，不把临时 IP URL 当完整 SSO 验收。
4. SQL/NAS 反向隧道由企业内网端主动连接新主机，须保留受限用户、密钥权限、精确远端监听限制和已核对 host key。只绑定回环/受控 Docker 私网，不开放公网数据库或 SMB。先验证目标通道，旧通道保持可回退；NAS 原件不复制到 ECS 或 OSS。

## OSS 跨 bucket/地域

读取 [文件存储与 OSS 迁移](object-storage.md)，迁移保留其应用隔离、私有访问、稳定对象键与无秘密日志约束。

- 新地域需要对应 Bucket/Endpoint、RAM 资源范围、CORS、加密/版本/生命周期及备份配置；内网 Endpoint 只供同地域服务使用，浏览器签名必须使用可达的公网入口。IMM、预览/Office 与回调也须按实际服务配置复验，不能只改上传 Endpoint。
- 完整列举所有实际使用前缀及数据库引用；控制台容量计数或 0 字节显示不是空 Bucket 证据。保留对象元数据、内容类型和业务键；若业务引用历史版本，须迁移/映射对应版本，不能只复制当前对象。
- 首轮复制与最终增量分开。最终冻结写入时重新列举并校验对象数量、总字节和每个对象内容摘要，处理删除标记和数据库缺失引用。分片 ETag 不能普遍充当 MD5；不得用抽样代替所承诺的完整性校验。
- `configure-oss-gateway` 在已有 `oss-gateway` release 时拒绝直接改变 Bucket/地域，这条护栏必须保留。普通部署、删 release、重跑 provision、手改 JSON 或新增 `--force` 不能替代迁移。
- 现有 OSS release 切换须使用针对真实状态实现并测试的管理员入口：核验受管 release/身份、源配置摘要、最终对象清单与无在途写入；持久备份旧网关配置、Runtime 与身份库；保留原应用令牌/前缀；切换候选网关与 Runtime 后执行真实 CRUD、匿名/越权拒绝、历史文件读取和冻结镜像健康。步骤失败须恢复旧网关与 Runtime，不能留下新网关配旧 Runtime。入口尚未完成或证据不充分时停止切换，继续复制/验证等独立工作。
- 不把网关探针成功说成存量对象迁移完成；不把 Skill 文档或发布包当成已安装的 Runtime helper。两者分别记录 SHA、命令和运行验证结果。

未启用版本且恢复至隔离候选的 `apps/` 网关可使用 [离线候选机 OSS 换域入口](oss-scope-candidate.md)，其前置清单和实例隔离必须从真实状态生成。不符合范围的环境须另行实现并测试，不能伪造输入绕过。

## 接管和回退

最终收口暂停源业务写入及后台任务，复制最后数据库/对象增量，通过一致性检查后才切换入口和 Runtime 主动登记。DNS 有缓存，源站须继续转发到唯一写入主站或提供明确维护只读状态；不能允许新旧各自写入。记录切换时间、DNS 值、实际响应节点与唯一任务执行位置。

旧origin转发应逐Host验证SNI、证书链和TLS会话行为，保留方法、请求体、SSO日志关闭及原超时，不用关闭证书校验解决问题。HTTP-01续期仍可能访问旧缓存节点时，受控转发该ACME路径到唯一目标。临时复用的PEM只证明当前TLS可用，不代表目标已有正规证书lineage或续期；可以先放独立临时目录，避免占用目标certbot的live路径，再按真实可达的challenge和目标管理入口单独完成签发、切换与续期验证。

目标接收写入前可恢复源配置/入口；目标已经产生新数据后，先停写并把目标增量和对象同步回源、校验引用，再回切。只恢复旧镜像或 DNS 不能恢复新写入。旧实例、Bucket、快照和凭证在观察及恢复验证完成前保留；迁移授权不自动等于立即释放全部旧资源。

验收覆盖电脑/手机登录、模块单击进入、SSO/iframe/统一助手、角色拒绝、旧文件/新上传/预览/下载/删除、SQL/NAS 最终容器访问、定时任务与备份恢复。记录真实测试环境，浏览器模拟不能替代真机。完成后更新部署规则、企业交接 Skill 与中央目录（Runtime ID 为主、源/目标地址按状态保留），经稳定 Release 和无缓存 `resolve` 验证后再报告 Skill 对其他业务 AI 可用。
