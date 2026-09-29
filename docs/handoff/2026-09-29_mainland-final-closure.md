# 企业内网与主备份收尾

责任归属：服务器、备份和内网传输由部署基础设施负责，SaaS 与子系统分别负责员工入口和业务页面。本仓只同步企业交接事实及 NAS 随包脚本；没有再次构建或发布业务服务，没有改变账号、授权、Runtime 身份、数据口径或共享 ACL。

## 已验证的运行状态

- 主 ECS 正式每日备份在 2026-09-29 12:19:51 CST 全链成功：8 PostgreSQL 实例 / 17 库、7 Redis、3 SQLite，263,981,391 bytes，SHA-256 `675158fe6ae0a5ef919ad0ea37b6f6452e8ca8138473c5a920219325a9687f70`。杭州备份桶 private、版本控制开启、AES256；精确版本完整 GET 与本地匹配，timer active/waiting。同地域机外备份不等于跨地域容灾或全系统恢复演练。
- Windows goods HTTP 任务直连杭州 `101.37.173.94:22`，业务容器读取 200 / 883 行；正常同步 13:01:48 CST `ready/error=null`。SQL 任务直连 `47.97.90.161:22`，13:12:40 CST `H_TRADE` 真实只读查询通过，增删改权限 0。
- NAS 两个 worker 直连杭州 SSH 22，用户 `zjnas-tunnel`，原 key 文件名保留。13:14:49 CST 两主机允许的四共享目录可读、两拒绝共享仍拒绝；生产最终 NAS 容器四共享有界读取通过。goods NAS 私网恢复不等于商品业务新增 NAS 功能。
- Windows 原机外备份 pull 改新 goods，13:02:40 CST 退出 0；归档 281,323 bytes 与 bundle 108,658 bytes 的 SHA 匹配，E 盘保留策略不变。
- 13:32:21 CST 两临时 bridge unit、目标专用 key / known_hosts、源端对应公钥及迁移 sshd 配置已精确撤除；sshd 语法检查后 reload。源临时账号保留 locked/nologin 且无公钥，原 LAN/NAS keys、旧 DNS 缓存转发、备份和实例不删除。

证据为受控迁移审计目录的 `main-backup-verified-20260929.json`、`lan-cloud-bridge-retirement.json`、`lan-windows-status-final.json`；公开规则只记录聚合结果，不复制客户资料、对象 key、版本 ID 或密钥。部署规则仓库同名最终交接保留详细时序。

## 发布范围与验收边界

本次准备 SQL `1.1.2`、goods `1.0.2`、NAS `1.0.3`，从审查合并后的干净 main 构建 `bundle-v1.4.26`。core `1.1.25` / legacy `1.2.0` 与之前 ZIP 应完全相同；发布、九份公开资产校验及本机 managed 更新均以实际执行后的记录为准，本候选不预先声称发布。

NAS 脚本只替换两处目标 IP，保留原密钥路径、用户、严格 host key 校验和自动重连逻辑。三个 Skill quick_validate、NAS `bash -n`、差异检查已通过。没有通用模板或契约变动，不需要重发 SaaS 或任何子系统。

13:29:49–13:31:08 CST 真实员工在电脑和手机触摸模拟各打开四模块，8 次均出现实际业务正文，手机一次 tap。电脑单样本 4.901 / 2.227 / 2.880 / 2.857 秒，手机 4.790 / 8.983 / 4.223 / 3.516 秒；不是均值、SLA、压力测试或真机结果。生产协同手机仍有 718 px 内容溢出，SaaS `global-check` 仍有 429，不能把迁移完成表述为 UI 缺陷已修复或所有模块秒开。证据见 `browser-verification/lan-final-browser-20260929.md`。
