# 服务器访问

## 2026-10-25 同企业归并候选：尚未切换

管理员已授权把`101.37.173.94`的商品动销看板和设计灵感库迁到已有`47.97.90.161`，目标默认Runtime为`aifabei-hk-01`，组织仍是`65130a23-b05e-4026-9615-761ab2d4193c`、environment为staging。本草稿仅记录初始约13GB私有副本与镜像准备；SaaS新能力正式上线、源48正常停用、最终DB/文件同步、域名和真实用户验收尚待Root完成。**当前源机仍是原业务权威；不得因catalog新增01/目标地址而在候选写业务或报迁移成功。**

保留目标原profile/登记key、现有全部应用、SQL/NAS通道；不把源`/etc/zhuojian/runtime.json`覆盖过去，不重init或ensure-app重建原app。商品动销原app ID`ef320cac-b9cc-4ab9-8ad1-5d88adb594f2`、两旧`*.hk48.aifabei.staging.zhuojianai.com`入口、原模块/Action/角色和local-managed文件保持。真正归属接管由SaaS实际cap、inactive源的原healthy commit重登与受管adopt-origin记录完成，不能只改IP或手写Runtime UUID。

待切换的HTTP通道保持同一道讯`10.0.0.94:8849`数据口径：Windows SYSTEM任务`Alphabet-Daoxun-Dashboard-Tunnel`仍用原任务身份/密钥/单活重连；目标方案为SSH22上的`127.0.0.1:18849`反向监听，经独立私网relay供`172.29.94.1:18849`访问。源`172.18.0.1`在目标属于商品360专属存储网，不能复用或让看板加入该网络。具体生效状态与限制公钥/known_hosts仅以Root最终回执为准；本草稿不声称客户端已改。

机外备份保留Windows任务`Alphabet-ZhuoJian-Backup-Pull`、每日04:00CST、脚本`C:\ProgramData\Alphabet\ZhuoJianBackup\pull-backups.ps1`、`E:\ZhuoJianBackups\aifabei-hk48`的原内容/保留策略。源只读SFTP是`zjbackup@101.37.173.94`、`/current/`，chroot`/srv/zhuojian/offsite-export`；切至目标前核其原只读边界、可信host key及实际下载/摘要。不能只搬两个SQLite而遗失Git、约8GB历史备份和latest export。源48/101选择器在成功后仅用于退役观察/回退定位，不能重新当新业务发布目标。

## 2026-09-29 杭州接管与内网直连

杭州 `101.37.173.94` 已恢复并启动商品动销业务，健康检查与同步 ready 通过；香港源 `47.243.48.78` 业务容器已停，旧入口反代杭州，避免 DNS 缓存产生双写。保留 `enterpriseKey=aifabei`、`runtimeId=aifabei-hk-48`、`organizationId=65130a23-b05e-4026-9615-761ab2d4193c` 和域名后缀 `hk48.aifabei.staging.zhuojianai.com`。`*.hk48` 记录已于 23:08:43 CST 切杭州，TTL 600；随后由总任务通过真实员工 SSO 打开模块验收，手机真机范围不由服务器 health 代替。

商品动销保留 `local-managed`，无企业 OSS 网关。Windows SYSTEM 任务 `Alphabet-Daoxun-Dashboard-Tunnel` 已改连 `root@101.37.173.94` 的 SSH `22`，保留 `-R 172.18.0.1:18849:10.0.0.94:8849`；数据口径仍是原道讯 HTTP API，不是 SQL 适配。实际业务容器 `/api/gd_shops` 返回 200 / 883 行，正常 `sync-api` 于 2026-09-29 13:01:48 CST 完成，状态 `ready`、`error=null`。13:32:21 CST 杭州临时 HTTP 中继已停用并删除专用 unit / key / known_hosts，香港源对应公钥和迁移 sshd 配置已撤除、语法检查后 reload；原 LAN keys 保留，临时源账号保留 locked/nologin 且无公钥。

公司 Windows 原机外备份拉取任务也已改为新 goods 主机，并核验新 host key；2026-09-29 13:02:40 CST 任务退出 0，拉取 1 份 281,323 bytes 归档和 1 份 108,658 bytes bundle，SHA 均与源元数据相符。E 盘既有保留策略未改；这与主 ECS 上传杭州 OSS 的每日备份是两个独立流程。

本文件只记录识别信息和访问边界，不保存登录口令、私钥、令牌或本机访问档案。

## 企业 ECS

- 用途：承载商品动销看板与灼见 Runtime
- 地址：`101.37.173.94`（杭州；旧 `47.243.48.78` 保留观察和回退资料，不再作为内网数据中继）
- 登录用户：`root`
- 管理员初始化：已于 `2026-09-10` 完成，日常维护不得重复执行

连接时按 `$zhuojian-subsystem-builder` 的服务器长期访问记忆复用本机 SSH 档案。档案不存在时，按总 Skill 的首次接入规则尝试 SSH `22`，再尝试管理员配置的 `443`；只允许在当前用户明确授权的范围内建立访问记忆。连接失败先区分网络、端口、密钥和认证问题，不自动重置服务器凭证。

这是中国杭州阿里云轻量应用服务器。连接服从全局规则并走直连，不套用国外网站代理。

## Alphabet 内网服务器

- 用途：连接道讯只读网关，并维持到 ECS 的反向隧道
- 地址：`10.0.0.181`

该地址只能从可达 Alphabet 内网的设备或 VPN 连接。连接超时通常说明当前网络不具备内网路由，不代表认证信息错误。不要把该主机当作看板 Web 服务器，也不要抓取或搬运与商品动销看板无关的文件。

道讯网关认证保存在 ECS 的应用环境中。检查服务时只确认所需变量存在且进程能够使用，不读取、不复制、不回显其值。

## 授权边界

服务器访问只用于负责人明确提出的商品动销看板查看、排障、修改、发布和数据链路维护。删除数据、重置密码、重建隧道、重新初始化 ECS 或操作其他系统，不属于日常交接授权。
