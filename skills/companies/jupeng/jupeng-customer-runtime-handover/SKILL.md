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

## CRM 状态
上传的是空客户引导源码和本机构建制品，不含真实客户、邮件、附件和密钥。现有代码仍有单人JSON存储、回环Origin、Windows受保护凭据和自有AI连接假设。必须按总Skill完成统一身份、逐业务操作授权、持久存储及SaaS模型委托适配后才能上线。安装Runtime、构建制品已上传或探针健康，都不代表客户业务已接入。保留旧本机及Sites入口，不以公开Vite端口代替企业发布。

## 备份和接续
初始化前已对协作库全refs、上传制品和现有配置取受控快照，下载到获权管理员电脑并独立恢复文件、Git及全部refs。受控回执位于管理员本机 .codex/private/customer-initialization-20261029；服务器副本在 /root/customer-preinit-backups。原始归档可能含配置秘密，不放Git、公共交接包或回复。
这证明初始化前代码与配置的机外恢复，未证明未来业务数据库、附件或自动OSS保护。后续发布须按实际数据位置备份并验证恢复，保留旧有效点。现场doctor、双应用隔离、模块登记、业务SSO和真实用户验收分别记录在项目库；不要把这份Skill发布当作应用已部署。
