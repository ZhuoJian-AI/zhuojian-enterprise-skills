---
name: jupeng-product-runtime-handover
description: 飓鹏产品与供应商独立服务器的源码、统一身份与持久化交接。仅匹配 jupeng-product-hz-01 / 47.98.203.195，保留本机私有数据边界、product01协作库和已登记应用身份。
---

# 飓鹏产品与供应商服务器

先核对服务器实际Runtime档案：enterpriseKey=jupeng、runtimeId=jupeng-product-hz-01，当前公网地址47.98.203.195。不是共享ERP或客户CRM服务器，不复用其他Runtime的应用或登记凭据。

## 协作与源码

Git真源是/srv/jupeng/product/repo.git。先读全部任务分支、仓库AGENTS、STATUS、CHANGELOG及最近sessions，不因main曾经只有协作规范而覆盖任务分支业务代码。保留product01个人SSH和管理员长期访问；SSH/sudo维护身份不代表员工业务权限，也不从账号名推断自然人映射。

原共享业务在apps/product-web；原本机预览只绑定回环，不可改为公网服务。云端生产适配在apps/product-cloud，保留原业务核心和页面，通过scripts/build_cloud_projection.py投影、校验和维护。原业务已明确排除本机正式数据库、实际图片/合同、工厂价格和提成代码，不能因上线自动上传或把私有模块改成隐藏页一起传。历史报价/共享资料仍须按明确选择导入。

Runtime规范目录/srv/zhuojian/repositories/jupeng-product-library是apps/product-cloud的部署投影，不是另一套业务真源；image-provenance.json保留原协作提交、子树提交和已验收prebuilt身份。实际运行源码以Runtime release.json和平台登记为准，不用本文旧版本覆盖后续发布。更新先合并最新业务来源，重建对应镜像并保留投影历史，不能复用旧prebuilt冒充新代码。

## Runtime与接入

Runtime使用标准SSH22，Docker/Nginx/Compose/certbot已安装。标称2GiB、实际约1.6GiB、无swap；sourceBuild=false、maxConcurrentBuilds=1。本机或获准构建环境完成源码构建，服务器只组装已核对prebuilt镜像；不增swap、不在小机并发编译。

当前域名后缀product.47-98-203-195.sslip.io是已验收的接入验证域名；正式域名变更另核DNS、证书、Runtime和应用归属。product-library应用UUID为607c4cdb-f45f-4736-99dc-da8a95ee42c7，模块product-workbench，页面product-workbench.list；企业统一登录、实时session-check及原生2.5签名Action，不新建子系统员工账号或模型路由。直接旧POST接口不作业务入口，文件/报价下载仍需专用download能力。

两个初始化探针product-probe-a/product-probe-b保持停用、助手关闭、零员工授权，不重用其他服务器的探针或为真实员工授探针权限。新发布沿用实际应用身份、凭据和数据挂载。正常发布保留Runtime与原协作deploy.lock的串行保护、精确SHA和expected-current-commit检查。

## 数据与恢复边界

身份会话/确认/请求账本是/data/subsystem.db；原产品共享业务及图片、供应商附件正文在同一挂载旁的/data/product.sqlite。实际路径以release和容器挂载回读为准，不能只备份模板files目录。业务写入与持久回执共用product.sqlite事务，身份账本中断后同请求编号重试不会重复写入；不同数据库之间不宣称分布式原子事务。

保留local-managed格式。尚未迁移OSS，不把SQLite附件正文当成已进文件网关。备份须用SQLite Online Backup API覆盖两个实际数据库，连同文件目录、私有配置、Runtime release与可恢复Git全部refs；内容只进获权私有机外位置。当前平台Runtime storage-profile机器路由返回404，自动云保护未配置；不能把磁盘timer或一次手工机外恢复称为自动OSS备份。恢复和未来预绑定均按现场能力重新核对，不轮换其他Runtime凭据。

负责人仅需业务专用角色，既有学习/员工角色保留，不因维护权限授全企业研发者或管理员。临时验收账号必须在结束后撤权停用，真实负责人本人登录、改密和真机验收单列；隔离授权模拟、技术预检和真实SaaS验收不能互相替代。
