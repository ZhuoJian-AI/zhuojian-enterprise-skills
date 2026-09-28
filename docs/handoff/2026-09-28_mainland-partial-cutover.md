# 企业主机接管与过渡依赖

责任：业务子系统运行主机和企业 Runtime；Skill 同步交接规范。本文件记录两个企业主机先行切换；随后主平台接管与员工验收见 [最终交接](2026-09-29_mainland-active.md)，不要把本历史阶段当成当前主平台状态。

2026-09-28 两个杭州轻量主机已按原应用身份接管：goods 源业务已停，新端健康、同步 ready，旧 nginx 反代新端；production 三业务以原镜像启动，health/HTTPS/TLS 全通过，旧所有容器停止并以 nginx 反代新端。Runtime IDs、组织、slug、域名和授权身份保持，管理地址更新到实际目标。

Production OSS：266 对象、90,128,812 bytes，完整枚举、逐对象大小/CRC64/content metadata 相同；最终源业务/网关/写任务停止并收口 SQLite/registry 数据后，helper `e002459b5bcd4d35bda7a117554d0c8f` 提交杭州 scope，7 项真实隔离与读写 probe 通过，已有 app token/release 不变。恢复归档曾将 registry 目录 0700 丢成 0755，按源修复后完整回退与重试通过；迁移临时全桶枚举 RAM 权限在 probe 前已撤，不绕过 outside-prefix 护栏。

内网还未直连杭州：goods 保持原 HTTP 协议经旧 goods 中继，生产 SQL/NAS 经旧 production 受限 SSH 中继。旧 goods 已续费；明日企业内网维护需停临时桥释放端口、改客户端、验证业务读取后撤精确临时 key/单元。原 LAN/NAS keys 不删除，NAS 原文件不复制云端。

精确 DNS 记录已在云控制台核验：`*.hk48` 于 23:08:43 CST 指向杭州 goods，`*.hk01` 于 23:35:21 CST 指向杭州 production，TTL 600。两个新机真实 backup-all 运行成功并启用维护 timer；两旧机业务容器保持停止且 restart=no，临时数据桥仍 active。

源码/规则发布与服务器状态分别记录：迁移规范及交接已通过 PR #47、#48、#49 合并，稳定 Skill 尚待打包，不能把现行 stable 自动说成已包含本文件。

主迁移任务先完成真实员工 SSO 打开四个杭州子系统模块的验收，随后又在主 SaaS 切杭州后复验。该结果独立于服务器 health。生产协同手机页面仍有既存 overflow，本次主机迁移不修改 UI，不宣称该问题已解决；手机模拟与真机范围以总任务测试记录为准。
