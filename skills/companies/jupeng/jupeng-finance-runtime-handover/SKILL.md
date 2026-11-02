---
name: jupeng-finance-runtime-handover
description: 飓鹏财务服务器的源码、统一身份、数据与发布交接。仅匹配jupeng-finance-sg-01 / 47.237.128.65，保留现有业务和多人协作。
---

# 飓鹏财务服务器

先核对 /etc/zhuojian/runtime.json：enterpriseKey=jupeng、runtimeId=jupeng-finance-sg-01；当前地址47.237.128.65，新加坡。保留finance01的个人SSH和管理员专用连接，不重置密钥或密码。

## 源码与发布
Git真源是/srv/jupeng/finance/repo.git，先读取全部任务分支、AGENTS、STATUS、CHANGELOG及最近sessions。原业务在apps/finance-workbench；兼容适配在apps/finance-cloud，保留原业务核心，通过统一SSO和实时session-check访问。独立部署投影在/srv/zhuojian/repositories/jupeng-finance-workbench，applicationSlug=finance-workbench。投影不是第二套业务真源，image-provenance.json记录原协作提交、受测镜像和组装关系，运行提交必须回读release.json。

首次接入前已有/opt/finance-workbench和finance-workbench.service，原DB是其data/finance.sqlite3；/srv/jupeng-assistant也是存量，不得因为协作库旧STATUS写“未部署”就忽略或清理。原公网入口与旧服务的实际切换状态以最新Nginx、service及项目记录为准。统一接入后，旧密码、旧cookie和直接API不得绕过底座；原服务只能在已核实数据归属及恢复方案后用于恢复。

本机约1.6GiB且无swap，sourceBuild=false。依赖与代码在获准开发机测试，服务器只用已验证的固定依赖镜像做受控轻量COPY组装，不下载依赖、编译或增swap。不同Docker存储后端显示的镜像ID可能不同，必须用导出归档内Config实际字节摘要及源版本标签核对，不因标签相同就放行。已有Runtime和协作deploy.lock的双重锁、精确SHA及expected-current-commit保持。

## 统一身份和数据
云端仅使用SaaS稳定员工ID，财务业务专用角色只授权本系统精确页面与Action，不授全企业研发者/管理员。旧users表保留历史业务引用，不是云端员工登录来源；不得按姓名认领历史记录。兼容后端仅容器回环4317，由身份层发带短时绑定签名的内部请求，不接受旧本地cookie作为员工身份。

真实财务账套及附件正文为/data/finance.sqlite3，身份会话、确认、请求账本为/data/subsystem.db，均须在Runtime持久挂载内。保留原SQLite附件BLOB及原件摘要格式，未迁OSS；备份不能只归档模板files目录。下载完整账套用专用finance-workbench.download能力，不把二进制备份声明成标准分页数据集导出。查询、财务单据、复核、原件各自精确授权，账套版本和原command_log的防重复执行保留。

旧OCR脚本和/srv/jupeng-assistant不代表云端模型能力已接通；本次身份接入不自动部署历史独立AI交接包或复制模型Key。专业AI新增需求另按当前SaaS受控能力核对。

## 备份与验收
两份真实SQLite均用在线备份API，覆盖附件、必要配置、Runtime release及协作/投影全refs。初始化前的原代码、账套、SSH/Nginx与配置已有管理员受控机外恢复点，具体在项目私有回执查找；原始归档可能含秘密，不进Git。手工恢复不等于持续自动云保护，必须实时核对机器存储接口和timer，不假报OSS已配置。

真实入口、底座实点、四类凭证、普通角色允许/拒绝、撤权及数据保留分别验收。Runtime healthy或首次候选启动不是已登记；初始候选验证失败按1.1.52的精确未登记恢复入口处理，不清状态、不注册失败版本。
