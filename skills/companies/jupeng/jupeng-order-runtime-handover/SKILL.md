---
name: jupeng-order-runtime-handover
description: 飓鹏跟单服务器的源码、统一身份、数据与发布交接。仅匹配jupeng-order-hz-01 / 47.96.234.89，保留现有业务和多人协作。
---

# 飓鹏跟单服务器

先核对 /etc/zhuojian/runtime.json：enterpriseKey=jupeng、runtimeId=jupeng-order-hz-01，当前地址47.96.234.89。保留order01/order02/order03个人SSH与管理员访问；这些维护账号不直接当作员工业务身份。

## 源码与协作
Git真源是/srv/jupeng/order/repo.git；每次先读AGENTS、STATUS、CHANGELOG、最近sessions及所有任务分支，保留不同同事的未合并工作。原工作台在apps/trade-workbench，统一身份兼容适配在apps/trade-cloud，独立投影在/srv/zhuojian/repositories/jupeng-trade-workbench。applicationSlug=trade-workbench，底座名称“跟单协作工作台”，模块trade-workbench。登记应用UUID为f4f51bb1-f7c6-4458-a5b0-2dd45218d929，当前运行源与投影关系读release.json和image-provenance.json。

原独立IP HTTPS演示站配置在/etc/trade-workbench/site.json，静态版本在/var/www/trade-workbench，旧自动发布器及证书续期各有独立timer。不得把旧演示链接、旧发布状态或旧浏览器草稿当成底座已接入证据。统一入口切换时保留历史制品和用户草稿，核对旧Nginx及timer的当前状态，不自动恢复旧匿名程序入口。

## 程序与数据边界
目前保留原演示工作台和浏览器草稿，未接共享业务数据库、真实ERP或企业微信。底座SSO只负责统一入口和员工授权，不把静态演示数据变成已同步的正式业务。云端localStorage和IndexedDB按SaaS稳定员工ID分隔，当前用户不能被浏览器提交的姓名或任选ID替换；这是浏览器草稿隔离，不是服务端共享库或对同一设备调试者的秘密隔离。

新接入域名与原IP网页的浏览器原点不同，旧草稿和图片仍留在原浏览器。不得静默把旧数据归给新登录员工，也不能用空云端页面声称原数据丢失；迁移须经实际经办人选择导出/导入并核对附件。旧原点恢复页如存在，只用于本人取回本机数据，不作为程序登录通道。

统一登录、实时授权、撤权和Bridge由apps/trade-cloud承担；业务页面与现有内部导航保留。业务角色只授trade-workbench精确页面及本人范围，不授其他系统或全企业研发者。本次仅有工作台状态查询接口，不代表AI能读取浏览器草稿或执行未接的ERP/企微业务。历史独立模型/OCR包不自动复制或启用。

## 发布与保护
标称2GiB、实际约1.6GiB、无swap，sourceBuild=false；获准构建环境冻结源码和镜像，服务器只组装固定制品，保留协作deploy.lock及Runtime锁、精确SHA和expected-current-commit。原dist修改不会自动进入独立cloud投影，后续更新须合并最新原业务并重建/校验投影，不用落后模板覆盖。

身份/确认等服务端数据位于/data/subsystem.db及Runtime文件挂载；业务草稿、图片仍在员工浏览器，服务器备份不能覆盖这部分。机外恢复须包含真实数据、配置、release和两份Git全部refs，并区分手工点、自动任务及自然周期。桌面、手机视口、WebKit/真机、底座真实SSO及员工本人使用分别记证据，不相互替代。
