---
name: alphabet-daoxun-data-bridge
description: "在 Alphabet 的 8.218.208.205 ECS 上，通过既有反向隧道读取内网道讯 SQL Server 数据，并据此开发、部署和接入灼见 SaaS 子系统。用户提到道讯数据、H_TRADE、Alphabet 内网数据库、反向隧道或把相关看板嵌入 SaaS 时使用。"
---

# Alphabet 道讯数据子系统

本 Skill 是当前企业环境的交接层。构建、部署、统一登录、角色授权、Manifest、Action、iframe Bridge、OSS 和 SaaS 登记必须同时使用 `$aifabei-subsystem-builder`；本 Skill 只补充道讯数据通道的真实入口、只读边界和验收方法。

本 Skill 由 `ZhuoJian-AI/zhuojian-enterprise-skills` 稳定目录托管。每次任务先让 `$aifabei-subsystem-builder` 更新总 Skill 和本机交接 Skills；若本 Skill 被安装或更新，立即重新读取本文件及本次任务需要的 references，不使用更新前的交接事实。

## 版本声明

此前发出的旧版 `alphabet-daoxun-data-bridge` 已作废，不再使用。旧版只记录了反向隧道和 TDS 握手，仍把数据库认证、只读账号与 Docker 查询写成待完成；这些状态已经过时，会导致后续 Codex 错误地再次索要数据库账号或报告“只能通隧道、不能查数据”。收到本包后应删除或覆盖旧版，并以本包记录的已验证状态为唯一交接依据。

这里作废的是旧版道讯桥接 Skill，不是 `$aifabei-subsystem-builder`。前者负责道讯只读数据通道，后者负责业务系统开发、部署、OSS、权限与 SaaS 接入；涉及道讯的系统必须同时使用两者。

## 已知事实

开始工作先完整读取 [当前环境](references/environment.md)。不要重新猜测内网地址或把“ECS 不能直连内网 IP”误报成通道未打通。

- 道讯 SQL Server 位于 Alphabet 内网，内网服务器主动向 ECS 建立反向 SSH 隧道。
- ECS 上的入口是宿主机回环地址 `127.0.0.1:11433`；它转发到内网 SQL Server `1433`。
- `8.218.208.205 -> 10.0.0.181:1433` 直接访问失败是预期行为。这里没有整网 VPN、专线或网络磁盘，也不需要这些东西才能使用现有定点隧道。
- ECS 已配置专用 SQL Server 只读身份，并已从宿主机和临时 Docker 容器执行真实 `SELECT` 验收。该身份不是写入角色或数据库所有者。
- 凭证只保存在 ECS 的 root-only 集成配置中。本 Skill 不保存密码；不得把凭证写入 Skill、源码、Git、日志、Manifest、前端或回复。

## 工作流程

1. 先按 `$aifabei-subsystem-builder` 登录 `8.218.208.205` 并运行 Runtime 健康检查。
2. 在 ECS 宿主机复核 `127.0.0.1:11433`。需要确定性验证时，把 [check_tds_tunnel.py](scripts/check_tds_tunnel.py) 送入 ECS 的 `python3 -` 标准输入执行；该检查只做 SQL Server PRELOGIN 握手，不登录、不执行 SQL、不修改数据。
3. 若握手成功，状态写为“网络隧道已通”。不得因为 ECS 无法直接访问 `10.0.0.181`、没有 VPN 或没有网络挂载而推翻该结论。
4. 若握手失败，先检查 ECS 回环端口是否监听，再检查内网服务器上的专用隧道任务是否运行。只报告实际失败层级，不把传输失败说成数据库密码错误。
5. 真正读取业务表时，复用 ECS root-only 集成配置中的现有只读身份，不向负责人再次索要账号，不打印配置内容。先按 [只读接入与验收](references/read-only-access.md) 复核目标数据库、只读权限和最小样例查询。
6. 应用运行在 Docker 容器时，加入现有应用专属数据网络，并使用 [当前环境](references/environment.md) 中的 Docker 私网入口。不能把容器内的 `127.0.0.1` 当成 ECS 宿主机，也不得发布数据库端口到公网。
7. 在最终应用镜像和实际 Docker 网络内再次完成认证查询；测试镜像成功不能替代最终应用验收。兼容 SQL Server 2008 R2 时使用 TDS `7.0` 或驱动的等价兼容设置。
8. 道讯数据默认只读。查询、看板、统计和预警从道讯取数；子系统自己的配置、备注、流程状态、审计和缓存写入子系统自有数据库；业务附件使用 Runtime 当前 OSS 能力。
9. 通过 `$aifabei-subsystem-builder` 完成页面、统一 SSO、角色数据范围、Manifest、查询 Action、iframe Bridge、部署、登记和真实员工端验收。SaaS 不直接连接道讯数据库，只调用已登记子系统的受权 Action。

## 写入边界

用户曾明确要求道讯数据库不能被修改。因此普通看板或查询需求一律只读。只有用户在新的请求中明确授权写入，并且已确认道讯业务规则、官方 API 或规定存储过程后，才能另行设计写操作；仅有网络通道或高权限账号不构成写入授权。

不得用 `INSERT`、`UPDATE`、`DELETE`、`MERGE`、DDL、创建登录、授权、触发器或“执行后回滚”的写测试来验证只读能力。

## 完成标准

逐项报告，禁止合并成一句“已经打通”：

```text
tunnel_transport_pass   ECS 宿主机收到 SQL Server TDS PRELOGIN 响应
database_auth_pass      使用现有只读账号完成认证和只读 SQL
container_database_pass 最终应用容器通过私网入口完成同一只读查询
subsystem_contract_pass Manifest、SSO、权限过滤和查询 Action 通过
saas_embed_e2e_pass     真实员工从 SaaS 打开页面并看到获权实时数据
```

只有前五项全部通过，才可向负责人说“道讯数据子系统已经接通并嵌入 SaaS”。
