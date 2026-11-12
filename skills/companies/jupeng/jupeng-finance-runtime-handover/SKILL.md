---
name: jupeng-finance-runtime-handover
description: 飓鹏杭州财务服务器的源码、统一身份、数据与发布交接。仅匹配保留的jupeng-finance-sg-01 / 121.196.35.145，原新加坡已退役，保留现有业务和多人协作。
---

# 飓鹏财务服务器

先核对 /etc/zhuojian/runtime.json：enterpriseKey=jupeng、runtimeId=jupeng-finance-sg-01；2026-11-12 已由杭州121.196.35.145接管。runtimeId含sg是保留身份，不代表仍在新加坡。原47.237.128.65已停止财务容器、Nginx与旧备份调度并禁自启，发布凭据移出活动路径、Git拒绝推送；仅保留恢复资料，不作连接、发布或数据真源。保留finance01的个人SSH和管理员专用连接，不重置密钥或密码。

业务入口为https://finance-workbench.finance.121-196-35-145.sslip.io，员工仍从原灼见底座SSO进入。原Runtime UUID、application/release UUID与19条原授权在切换中保留。后续操作以现场Runtime和项目回执为准，不能依据旧IP或旧Skill重启源业务。

## 源码与发布
杭州Git真源是/srv/jupeng/finance/repo.git，先通过本人受信连接读main的README_MAINTENANCE.md、AGENTS、docs/ai-collaboration/README.md及财务协作Skill，再读相关任务分支、STATUS、CHANGELOG与最近sessions。本地已包含服务器提交时不重复fetch；缺对象或不能证明包含时才同步。每任务独立工作树和任务单。原业务在apps/finance-workbench；兼容适配在apps/finance-cloud，保留原业务核心，通过统一SSO和实时session-check访问。独立部署投影在/srv/zhuojian/repositories/jupeng-finance-workbench，applicationSlug=finance-workbench。投影不是第二套业务真源，image-provenance.json记录原协作提交、受测镜像和组装关系，运行提交必须回读release.json。迁移保留595464ee41908c1270ecb9cf51a9c66882824d46的完整运行镜像；协作main、投影HEAD和运行SHA可能不同，不能由旧投影目录重建覆盖当前功能。

首次接入前已有/opt/finance-workbench和finance-workbench.service，原DB是其data/finance.sqlite3；/srv/jupeng-assistant也是存量，不得因为协作库旧STATUS写“未部署”就忽略或清理。原公网入口与旧服务的实际切换状态以最新Nginx、service及项目记录为准。统一接入后，旧密码、旧cookie和直接API不得绕过底座；原服务只能在已核实数据归属及恢复方案后用于恢复。

杭州为2核、约891MiB内存且无swap，sourceBuild=false。依赖与代码在获准开发机测试，服务器只用已验证的固定依赖镜像做受控轻量COPY组装，不下载构建依赖、重型编译或增swap；新增OCR/导入负载须核实实时余量。不同Docker存储后端显示的镜像ID可能不同，必须用导出归档内Config实际字节摘要及源版本标签核对，不因标签相同就放行。已有Runtime和协作deploy.lock的双重锁、精确SHA及expected-current-commit保持。Gavin本机CI走独立COA-CI，数据放D:/CI/Jupeng-finance。

## 统一身份和数据
云端仅使用SaaS稳定员工ID，财务业务专用角色只授权本系统精确页面与Action，不授全企业研发者/管理员。旧users表保留历史业务引用，不是云端员工登录来源；不得按姓名认领历史记录。兼容后端仅容器回环4317，由身份层发带短时绑定签名的内部请求，不接受旧本地cookie作为员工身份。

真实财务账套及附件正文为/data/finance.sqlite3，身份会话、确认、请求账本为/data/subsystem.db，均须在Runtime持久挂载内。保留原SQLite附件BLOB及原件摘要格式，未迁OSS；备份不能只归档模板files目录。下载完整账套用专用finance-workbench.download能力，不把二进制备份声明成标准分页数据集导出。查询、财务单据、复核、原件各自精确授权，账套版本和原command_log的防重复执行保留。

财务报销云OCR沿用底座受控能力，采购识别与原界面随冻结镜像保留。旧OCR脚本和/srv/jupeng-assistant不代表另一套独立AI后台已接通；不得部署历史独立AI交接包或复制模型Key。专业AI新增需求另按当前SaaS受控能力核对。

## 备份与验收
两份真实SQLite均用在线备份API，覆盖附件、必要配置、Runtime release及协作/投影全refs。初始化前的原代码、账套、SSH/Nginx与配置已有管理员受控机外恢复点，具体在项目私有回执查找；原始归档可能含秘密，不进Git。手工恢复不等于持续自动云保护，必须实时核对机器存储接口和timer，不假报OSS已配置。

杭州当前在线入口为/usr/local/sbin/jupeng-finance-backup-online.py，jupeng-finance-backup-online.timer每天03:10执行，恢复点索引/srv/zhuojian/backups/finance-workbench-online/latest.json。原finance-backup曾指向停用的/opt账套，不能复活该旧调度；Runtime backup-all是离线入口，不能当作不停业务的日常在线备份。2026-11-12切换保留第87版与21份附件，两库完整性及附件摘要相同，机外完整读回、隔离恢复和Git独立克隆通过；这不代表已配置持续自动云备份。证据见杭州Git的迁移session与release-evidence/hangzhou-migration-20261112.json。

真实入口、底座实点、四类凭证、普通角色允许/拒绝、撤权及数据保留分别验收。Runtime healthy或首次候选启动不是已登记；初始候选验证失败按1.1.52的精确未登记恢复入口处理，不清状态、不注册失败版本。
