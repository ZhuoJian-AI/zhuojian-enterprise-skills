# 道讯研发取数与子系统开发

本页适用于Alphabet的系统研发者：通过同一个企业插件读取道讯和开发资料，或在已有独立服务器开发授权时使用维护CLI。安装Skill不授予权限，员工接入通道不等于普通员工角色。新业务系统仍按其真实员工授权过滤数据。

## 插件入口

核对本人企业和实时能力目录，搜索`business_tools.daoxun_sql`。五个只读Action：catalog目录、describe字段/主外键、query通用查询、page后续结果、guide完整开发指引。所有ID、Schema摘要从本轮发现取得，不用旧聊天中的摘要。先前撤下这些动作属于历史阶段；本轮按负责人最终确认恢复研发者获权接入，最终部署状态以真实目录和调用回执为准。

- catalog：传limit（1—200），可选search；返回真实表/视图及估算行数。
- describe：传object、limit，可选schema（默认dbo）；读取字段、类型、精度和主外键。
- query：传sql、limit，可选parameters和maxRows；使用SQL Server 2008 R2单条SELECT/CTE/联表/聚合，值写@name并在parameters绑定。
- page：传nextCursor和相同limit；不重跑SQL，完整读取各页，不把首屏当全部结果。
- guide：传limit=1；默认返回说明与availableReferences，传reference可读取完整zhuojian-subsystem-builder正文、引用文档及文本模板，也可读取Alphabet企业交接。它是包内资料读取，不是任意服务器文件访问。

真实经营库为smartlink。原H_TRADE仅11张表，不代表经营数据范围；2026-11-08元数据发现1092个非系统业务对象。工具没有业务表/字段白名单，具体字段含义和统计口径仍须核对。无DLP/PII内容审查或自动脱敏。

每个Action均声明精确permissionPolicy，不从普通业务角色的应用级权限自动继承；系统研发者由SaaS维护受管授权。当前有效角色、Action启停、OAuth范围、数据范围和授权版本在发现及调用时分别核验，SQL身份始终只有SELECT，无ERP增删改/执行或数据库管理权限。数据库凭据留在服务端。

## 查询与结果

maxRows默认10000，最多100000行/64MiB，超资源整体失败，不返回截断统计。大结果可聚合或按业务条件拆批。结果data为行数组，按columns同序解释；Decimal/大整数保持字符串精度，二进制以base64:表示，日期保持源值。游标15分钟有效，绑定本人/企业/授权版本；分页是同次查询结果，不宣称数据库事务一致性快照。

常用会计日期FSCL_DATE，期间通常含起日不含止日；库存为当前快照，不当历史库存。RLB/RLB_DTL/RLB_PAY常按SHOP_ID+RLB_NUM关联，PRODUCT.PROD_CLS_ID关联PROD_CLS。实际物理外键未必齐全，不能仅按列名推测单据口径或聚合粒度。

## 研发执行

本轮先补通用取数和开发资料，宿主AI可在本机已授权环境写代码、计算、测试和生成预览。服务器文件、命令、依赖、构建、截图及发布只有真实工具已提供并验证时才能宣称可用；查询Action不冒充服务器执行器。

已有SSH开发授权的环境继续按搭建Skill维护企业服务器，入口zhuojian-daoxun-readonly catalog/describe/query/page/guide，JSON参数从标准输入读取。维护CLI为root0700，配置仅留服务器root600；其身份与插件本人分开审计，不下发root或数据库密码。

当前企业服务器47.97.90.161 / aifabei-hk-01，既有11433隧道和172.29.181.1:11433私网入口保持。源码、镜像、Skill、权限和本人WorkBuddy验收分别报告，不因文档或角色名称声称系统已上线。
