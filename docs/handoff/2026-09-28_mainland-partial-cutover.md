# 企业主机接管与过渡依赖

责任：业务子系统运行主机和企业 Runtime；Skill 同步交接规范。SaaS 主平台、版本化文件桶与真实员工双端验收仍由总迁移任务记录，本文件不宣称它们完成。

2026-09-28 两个杭州轻量主机已按原应用身份接管：goods 源业务已停，新端健康、同步 ready，旧 nginx 反代新端；production 三业务以原镜像启动，health/HTTPS/TLS 全通过，旧所有容器停止并以 nginx 反代新端。Runtime IDs、组织、slug、域名和授权身份保持，管理地址更新到实际目标。

Production OSS：266 对象、90,128,812 bytes，完整枚举、逐对象大小/CRC64/content metadata 相同；最终源业务/网关/写任务停止并收口 SQLite/registry 数据后，helper `e002459b5bcd4d35bda7a117554d0c8f` 提交杭州 scope，7 项真实隔离与读写 probe 通过，已有 app token/release 不变。恢复归档曾将 registry 目录 0700 丢成 0755，按源修复后完整回退与重试通过；迁移临时全桶枚举 RAM 权限在 probe 前已撤，不绕过 outside-prefix 护栏。

内网还未直连杭州：goods 保持原 HTTP 协议经旧 goods 中继，生产 SQL/NAS 经旧 production 受限 SSH 中继。旧 goods 已续费；明日企业内网维护需停临时桥释放端口、改客户端、验证业务读取后撤精确临时 key/单元。原 LAN/NAS keys 不删除，NAS 原文件不复制云端。

源码/规则发布与服务器状态分别记录：本次交接修改尚需合并和稳定 Skill 打包，不能把现行 stable 自动说成已包含本文件。真实员工、手机真机与 DNS 最终收口未据服务器健康自动验收。
