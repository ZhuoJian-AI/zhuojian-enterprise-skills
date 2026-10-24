# 服务器访问

## 2026-10-25 已接管至01，源48退役观察

商品动销看板与设计灵感库已从 `101.37.173.94` 归并至既有 `47.97.90.161` / `aifabei-hk-01`。组织仍为 `65130a23-b05e-4026-9615-761ab2d4193c`，environment 为 `staging`；没有重建企业、覆盖目标默认 profile 或重新初始化服务器。原48 Runtime 已正常停用，源两业务容器均 exit 0、restart=no，源备份定时任务停用；源数据、Git、历史备份和失败/续程证据保留观察，不作为当前写入或发布目标。

最终数据传输为 1,846,927,360 bytes，流 SHA `b812cd28e143e055ff5cdcf4170d2324c9936234def574109a2e4926c008fb42`；目标按两个应用的完整文件清单、SQLite integrity 和原镜像/Git 校验后启动。商品动销仍是原 app `ef320cac-b9cc-4ab9-8ad1-5d88adb594f2`；设计灵感库仍是 `f61677f7-a6d2-4933-b4bb-6bbe33b1b8ac`。正常 SaaS 登记后两者 owner 已为目标 Runtime UUID `647b9a49-0e41-4c9a-aafa-052530b73640`。九应用的原 app ID、origin、commit、Manifest、Action、角色和四类项目凭据精确比较通过；迁入应用保持 `local-managed`，没有转换 OSS。

两个 `*.hk48.aifabei.staging.zhuojianai.com` 旧 HTTPS origin 保留，不改成 hk01 域名。`*.hk48.aifabei.staging` 的 A 记录已于 `2026-10-25 05:18:23 CST` 在授权 RAM 控制台保存为 `47.97.90.161`，TTL 600。DNS 缓存仍到源101时，由源 Nginx 向目标唯一业务节点转发；该实际链路启用正确 SNI、证书验证、验证深度3并关闭 upstream TLS session reuse。不能为排障关闭证书验证，也不能恢复源业务造成双写。

HTTP 数据仍来自道讯 `10.0.0.94:8849`，与 SQL 口径分开。Windows181 的原 SYSTEM canonical 任务 `Alphabet-Daoxun-Dashboard-Tunnel` 已切至目标 SSH22，反向监听仅 `127.0.0.1:18849`，经独立 `zhuojian-goods-http-readonly` 网络和 relay 提供 `172.29.94.1:18849`。`2026-10-25 05:29:52 CST` 三轮宿主机/实际商品容器共6次 `/api/gd_shops` GET 均200、885行、92,971 bytes，内容 SHA 均为 `f2f1efd23ead0f5d44856873f41b36d195a0729fbf73d18f3a2bf786923805f1`；公网18849无监听，旧Source18849 SSH不再运行。目标 `172.18.0.1` 属商品360存储网络，不能借用。helper 与该看板逐应用 root 审批网络记录已经安装，后续 deploy/rollback 仍须保持已批准补充网络与原主网，不能只临时 network connect。

### final_acceptance（2026-10-25实际收口）

- `http_canonical`: passed，以上真实三轮证据；日常任务仍实时检查监听、同步时间和错误。
- `native_backup_and_restore`: passed，原生九应用本轮归档、commit、metadata及一致快照标志逐项核对，原服务均恢复；两个迁入归档完整SHA及全部成员流校验通过，数据库家族实际恢复至私有tmpfs，SQLite integrity与外键检查通过后清除。未把这一检查称为重新部署全部业务后的用户整轮验收。
- `offsite_sftp_windows_ack`: passed，Windows原任务于06:10:17 CST为Ready/LastResult0；八文件完整SHA与目标一致，受限ACK为同一manifest `15caeb14385ab4995c41000c15da5bbcb9b3c608defd441343d2652c2512069f`。原SYSTEM原生日程、E盘路径和历史保留；CIM导出误报由原生COM完整任务定义对照澄清，未放宽身份核对。
- `target_letsencrypt_renewal`: passed，两旧域目标正规LE lineage已签发，证书到期2027-01-22，线上leaf与canonical DER一致；两次原生renew dry-run及限定deploy hook通过。首次生产secondary连接超时证据保留，两个staging门通过后才续程签发。本次ACME子进程用临时代理，已清理；原certbot timer继续既有direct配置，无临时端口依赖，未来自然到期续签仍按实际周期观察。
- `employee_and_mobile_e2e`: 本轮未做新的员工页面/手机真机验收，不沿用服务器 health 冒充。

机外备份保留原 Windows 任务 `Alphabet-ZhuoJian-Backup-Pull`、每日04:00 CST、`C:\ProgramData\Alphabet\ZhuoJianBackup\pull-backups.ps1`、`E:\ZhuoJianBackups\aifabei-hk48` 历史与保留策略，改从 `zjbackup@47.97.90.161` 只读 `/current/` 下载。原Action现在进入逐八文件校验并发送受限ACK的wrapper；原pull代码只改主机，私钥未复制。目标两应用按ACK保留最近两点及两代导出；本轮实际各生成一个新恢复点，未发生旧点裁剪。整批原生backup.service在空间不足或最新点未获ACK时暂停本轮备份，包含原七应用，业务服务继续运行；不能把这个门禁说成仅影响迁入应用。

恢复和异机ACK通过后，仅清理目标本轮initial-staging内124个与源逐文件SHA/inode匹配的历史重复副本，释放11,782,852,455字节，目标空闲24,260,608,000字节。源全部原件和Windows历史、正常九应用备份/导出保持；此前242个初始重复数据文件也仅清目标自有副本。临时复制授权已精确撤除，HTTP/ACK及其他原公钥保留。Source48/101及更早香港地址只用于历史、观察和受控回退定位，不能重新初始化或发布新业务。

## 2026-09-29 杭州接管与内网直连

杭州 `101.37.173.94` 已恢复并启动商品动销业务，健康检查与同步 ready 通过；香港源 `47.243.48.78` 业务容器已停，旧入口反代杭州，避免 DNS 缓存产生双写。保留 `enterpriseKey=aifabei`、`runtimeId=aifabei-hk-48`、`organizationId=65130a23-b05e-4026-9615-761ab2d4193c` 和域名后缀 `hk48.aifabei.staging.zhuojianai.com`。`*.hk48` 记录已于 23:08:43 CST 切杭州，TTL 600；随后由总任务通过真实员工 SSO 打开模块验收，手机真机范围不由服务器 health 代替。

商品动销保留 `local-managed`，无企业 OSS 网关。Windows SYSTEM 任务 `Alphabet-Daoxun-Dashboard-Tunnel` 已改连 `root@101.37.173.94` 的 SSH `22`，保留 `-R 172.18.0.1:18849:10.0.0.94:8849`；数据口径仍是原道讯 HTTP API，不是 SQL 适配。实际业务容器 `/api/gd_shops` 返回 200 / 883 行，正常 `sync-api` 于 2026-09-29 13:01:48 CST 完成，状态 `ready`、`error=null`。13:32:21 CST 杭州临时 HTTP 中继已停用并删除专用 unit / key / known_hosts，香港源对应公钥和迁移 sshd 配置已撤除、语法检查后 reload；原 LAN keys 保留，临时源账号保留 locked/nologin 且无公钥。

公司 Windows 原机外备份拉取任务也已改为新 goods 主机，并核验新 host key；2026-09-29 13:02:40 CST 任务退出 0，拉取 1 份 281,323 bytes 归档和 1 份 108,658 bytes bundle，SHA 均与源元数据相符。E 盘既有保留策略未改；这与主 ECS 上传杭州 OSS 的每日备份是两个独立流程。

本文件只记录识别信息和访问边界，不保存登录口令、私钥、令牌或本机访问档案。

## 企业 ECS

- 用途：承载商品动销看板与灼见 Runtime
- 当前地址：`47.97.90.161`，Runtime `aifabei-hk-01`；`101.37.173.94` / 原48已停用观察，更早 `47.243.48.78` 只作历史定位。
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
