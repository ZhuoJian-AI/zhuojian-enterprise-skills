# 服务器通用只读查询

适用于已经获得 Alphabet 企业服务器开发授权的 AI，配合 `zhuojian-subsystem-builder` 取数、开发和验收子系统。Skill 是指引，不授予 SSH/root/数据库权限，不向普通员工插件分发开发身份。复用开发环境自己的既有服务器访问登记；不向业务负责人重复索要已登记凭据。

## 当前可用入口

- 服务器：`47.97.90.161` / `aifabei-hk-01`。
- 经营数据库：`smartlink`；`H_TRADE` 是只有11张表的另一数据库，不能替代经营库。
- 命令：`/usr/local/bin/zhuojian-daoxun-readonly`，root0700。
- 说明：`/srv/zhuojian/handoffs/alphabet-daoxun-data-bridge/SKILL.md`。
- 源码：`/srv/zhuojian/worktrees/daoxun-general-readonly-20261108/business_tools/daoxun_sql.py`；实际镜像以 Runtime 当前记录为准，不用规范仓库旧 HEAD 覆盖运行代码。

命令读取受管镜像，在独立临时容器中执行维护查询，只连接现有 SQL 私网；不启动 HTTP、不开放公网端口。只读配置在服务器 `/etc/zhuojian/integrations/daoxun-smartlink-readonly.env`（root600），结果快照在 `/srv/zhuojian/maintenance/daoxun-readonly`（root700）。命令在服务器内部取用配置，不打印、不复制给模型或员工。

## 用法

JSON 参数走标准输入，返回真实 JSON。开发 AI 按目标自主选择目录、字段、查询或结果分页，不需要业务负责人写 SQL 或为每张报表登记接口。

```sh
printf '%s\n' '{"limit":200}' | zhuojian-daoxun-readonly catalog
printf '%s\n' '{"schema":"dbo","object":"PROD_CLS","limit":200}' | zhuojian-daoxun-readonly describe
printf '%s\n' '{"sql":"SELECT COUNT(*) AS styles FROM dbo.PROD_CLS WHERE YEAR_VAL=@year","parameters":{"year":2026},"limit":100}' | zhuojian-daoxun-readonly query
printf '%s\n' '{}' | zhuojian-daoxun-readonly guide
```

- `catalog`：当前非系统表/视图、Schema 和估算行数，支持 `search`。目录没有业务表白名单；2026-11-08共1092个业务对象，不等于所有字段口径均已核实。
- `describe`：列名、类型、长度、精度、可空、主键、外键和数据库中文备注。物理外键可能不完整，业务关联仍须核对真实单据。
- `query`：本库单条 SELECT、CTE、联表、子查询、聚合及集合查询。值写作 `@name`，在 `parameters` 中绑定；SQL Server 2008 R2不支持 OFFSET/FETCH、STRING_AGG 等新版语法。
- `page`：传返回的 `nextCursor` 与相同 `limit`，继续读取同次结果，不重跑 SQL；游标15分钟有效。所有页的 `data` 按 `columns` 同序解释，重复列名不会覆盖。
- `guide`：读取当前运行模块的简短说明。

`limit` 为每页1—200行，默认100；`maxRows` 默认10000，最多100000行/64MiB，超资源整体失败，不把截断数据当完整结果。大结果按真实业务条件拆批或在数据库聚合。Decimal/大整数保留字符串精度，二进制以 `base64:` 表示，日期保留源值。分页是一次查询结果，不宣称为数据库事务的一致性快照。

## 数据和权限边界

真实 SQL 登录只有 SELECT，无 INSERT/UPDATE/DELETE/EXECUTE/db_owner/sysadmin；每次连接再次核验。SQLGlot检查SQL结构和当前数据库，pymssql绑定值；无业务表/字段白名单、PII/DLP扫描、内容审查或自动脱敏。不执行存储过程或跨服务器数据源，不修改ERP。

经营报表常用会计日期 `FSCL_DATE`，期间通常含起日、不含止日；当前库存不能当历史库存。`RLB/RLB_DTL/RLB_PAY` 常按 `SHOP_ID+RLB_NUM` 关联，`PRODUCT.PROD_CLS_ID` 关联 `PROD_CLS`；具体状态、金额、退货和关联粒度须核对，不能仅按字段名推断业务口径。

开发 AI 可用这些真实数据实现业务系统，新的业务页面和查询服务仍须落实该系统的员工权限、租户隔离和数据范围。需要应用直接读SQL时，通过受控 Secret 注入现有专用只读配置、登记SQL网络附件并从最终镜像复验；不把开发维护入口、root或数据库凭据交给员工，不复制其他应用SSO/签名身份。

## 员工插件与开发入口

员工 MCP 仍只开放原来逐项获权的业务查询。`business_tools.daoxun_sql.*` 五个动作曾被额外登记，已于2026-11-08撤下；当前目录为0、旧调用404，员工Web服务不含SQL凭据或SQL网络连接。它们不是本开发入口的调用方式，不需要为本任务向普通员工扩权。

WorkBuddy 若是在做子系统开发，使用其已获权开发环境和本服务器命令；若仅安装员工企业插件，则不能由“读Skill”获得开发权限。两种身份不能相互替代。2026-11-08已验收服务器维护查询、完整目录分页、字段/主外键、参数化联表、聚合及员工入口撤下；具体新建系统、慧姐设备和新业务员工流程仍按该次目标验收。
