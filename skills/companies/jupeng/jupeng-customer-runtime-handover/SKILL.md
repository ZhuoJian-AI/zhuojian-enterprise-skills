---
name: jupeng-customer-runtime-handover
description: 飓鹏独立客户服务器的源码、协作与初始化交接。仅匹配 jupeng-customer-hz-01 / 121.43.59.104，保留既有客户 CRM 上传源、独立 SSH 账号与初始化前恢复点。
---

# 飓鹏客户管理服务器

先核对 /etc/zhuojian/runtime.json：enterpriseKey=jupeng、runtimeId=jupeng-customer-hz-01，当前公网地址121.43.59.104。不是共享机的 jupeng-hz-shared-01，不得复用旧 ERP 只读 Runtime 或其应用身份。

## 源码与人员协作
客户项目 Git 真源是 /srv/jupeng/customer/repo.git。先查看全部任务分支、docs/OWNERS.md、STATUS、CHANGELOG、sessions 和未合并任务。CRM 上传原始源码提交685a522b8fbba71a02f75a60be20cc417214df6f，来源分支 task/customer01/20261029-crm-cloud-upload；不可因 main 初期只有协作规范而认定没有业务代码。业务目录 apps/customer-crm，上传包另存在本企业 customer/artifacts 的该提交目录。任务基线以现场最新提交为准，不能将本文旧SHA覆盖后续进展。
已有 customer01 独立开发账号与个人密钥，保留其 authorized_keys 和管理员专用连接，不重置密码或全局 SSH。账号持有完整免密sudo；自然人与平台用户映射以企业私有项目记录及负责人确认核对，不由账号名或公钥注释推定。

## 初始化与发布边界
Runtime 标准 SSH 22，Docker/Nginx/Compose/certbot 已安装；档案和登记凭据在 /etc/zhuojian，秘密只留 root 受控文件。标准 Runtime 的受管仓库在 /srv/zhuojian/repositories，不能移动或清空原协作库来满足规范目录。
此实例标称2GiB，实测总内存约1613MiB且无swap：sourceBuild=false、maxConcurrentBuilds=1。源码编译及重型测试放获准开发/构建环境；不临时加swap、不在此主机启动并发构建。镜像/制品和源SHA必须可核对，不用latest替代固定版本。
当前登记域名后缀是 customer.121-43-59-104.sslip.io，属于接入验证域名。迁移到正式域名须按真实 DNS、HTTPS、Runtime 与应用归属流程操作，不只改字符串。Nginx 已将 server_names_hash_bucket_size 设为128以容纳该域名；原配置回退副本在root初始化目录。
初始化探针只用 customer-probe-a / customer-probe-b，登记必须 disabled、无员工授权。不重用飓鹏共享机已有 runtime-probe-a / runtime-probe-b，也不为测试给真实员工授探针权限。

## CRM 状态（2026-10-29，本段只作交接，现场版本优先）
客户CRM已以兼容模式接入：应用customer-crm，UUID 8d55cd16-b1a7-4db8-abf1-1dfccf74ff5c，入口 https://customer-crm.customer.121-43-59-104.sslip.io/crm。专属Runtime保持不变；实际运行版本在Runtime release.json核对。本次受测发布源码2b3bf965fc472100c43c3ddc7c3be293eedbb7e8，是协作库 apps/customer-crm-cloud 的部署投影；不把投影分支当原业务开发主分支。

Gavin明确要求不改王进原有内容：apps/customer-crm业务树仍为136e823fbeebd8985fb8f069825e131cdbed77e8，与157b347基线一致。独立cloud目录加入SaaS2.5身份网关、实时授权、私有Node运行适配、Linux邮箱凭据、保存确认/版本/防重与审计。未改原页面、业务文案、计划和资料规则；原页面的Arvin等固定展示不是当前操作者身份，真实身份取外层底座栏及服务端稳定ID。

源码为空客户库；原App空库直接读取customer.name会崩溃，外层仅增加首次真实客户建档入口，确认保存后再挂载原App，不注入示例客户。原本机模型配置、Windows外接盘/开机功能仍保留在原源码；云端不接收模型Key、不启动独立AI后台，顶部入口将目标带入底座同一个助手草稿，不能声称旧独立AI流程或外接盘能力已云化。Bridge刷新为保护原React草稿返回deferred，属于兼容模式。

Node业务服务仅容器回环4317，Python身份网关8000由Runtime发布。本应用/data挂载包含身份SQLite、操作账本、crm/workspace.json、crm/files、crm/mail-archive和加密邮箱凭据；沿用原磁盘格式，未迁OSS。未知保存结果的pending账本会停止新写入，先核对实际业务回执再由负责人处理，不自动删除或重放。小机只组装已校验固定prebuilt镜像，完整本地构建配方在Dockerfile.build，镜像和源码来源见image-provenance.json；重新改代码后必须重建，不能复用旧prebuilt标签冒充新源码。

王进（SaaS稳定用户ID 0aae9f16-bd00-42eb-8634-004884831f5f）仅新增客户CRM专用角色；原学习/员工角色保留，没有赋予全企业研发者或企业管理员。SaaS权限与customer01 SSH维护权限分开；全库操作范围固定只在本应用精确Action上。使用受控临时员工已核真实SaaS入口、工作区读取和统一助手草稿；王进本人现有账号实登、手机完整业务及WebKit以最新项目验收记录为准，不能把健康/登记/隔离测试替代本人业务验收。

## 备份和接续
初始化前已对协作库全refs、上传制品和现有配置取受控快照，下载到获权管理员电脑并独立恢复文件、Git及全部refs。受控回执位于管理员本机 .codex/private/customer-initialization-20261029；服务器副本在 /root/customer-preinit-backups。原始归档可能含配置秘密，不放Git、公共交接包或回复。
这证明初始化前代码与配置的机外恢复，未证明未来业务数据库、附件或自动OSS保护。后续发布须按实际数据位置备份并验证恢复，保留旧有效点。现场doctor、双应用隔离、模块登记、业务SSO和真实用户验收分别记录在项目库；不要把这份Skill发布当作应用已部署。
