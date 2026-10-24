# Alphabet 主机归并与 Skill44 实际交接

两业务的最终数据、运行镜像、SaaS归属与DNS主接管已完成，当前业务主机为47.97/01。备份恢复、机外ACK、证书续期和用户端验收按下表独立记录，不能把主接管完成扩写为全部验收或公开Skill已发布。本文接替[准备交接](2026-10-25_alphabet-server-consolidation-skill.md)中的初副本状态；本次没有新增前端或业务功能，手机真机未测。

## 已完成事实

- 源 `101.37.173.94` 的两原容器均 exit 0、restart=no，原48 Runtime inactive。源数据、Git、历史备份和两次失败/已审续程证据保留。源仅转发缓存到达的旧域名流量，不再作为业务写入或发布目标。
- 最终流1,846,927,360 bytes、242数据文件，SHA `b812cd28e143e055ff5cdcf4170d2324c9936234def574109a2e4926c008fb42`；两端长度/SHA一致。目标逐文件摘要/元数据和SQLite integrity通过，保持原镜像、Git与local-managed数据。
- 商品动销原app `ef320cac-b9cc-4ab9-8ad1-5d88adb594f2`、设计灵感库原app `f61677f7-a6d2-4933-b4bb-6bbe33b1b8ac` 正常登记后均属01 Runtime UUID `647b9a49-0e41-4c9a-aafa-052530b73640`；旧hk48 origin保留。`platform-migration-contract-comparison.actual.json` 九应用的ID、origin、commit、Manifest、Action、grant、四凭据及组织角色精确比较通过。
- 授权RAM页面于2026-10-25 05:18:23 CST保存 `*.hk48.aifabei.staging` A=`47.97.90.161`、TTL600。Source101对缓存流量的受控TLS转发已验证，实际设置正确SNI、depth3、session reuse off；没有关闭证书验证或恢复源业务双写。
- Windows181原canonical HTTP任务已接管目标。2026-10-25 05:29:52 CST宿主机回环与真实商品容器三轮共6/6 GET200，885行、92,971 bytes、SHA均为 `f2f1efd23ead0f5d44856873f41b36d195a0729fbf73d18f3a2bf786923805f1`；公网18849无监听，旧Source18849 SSH不再运行。目标既有SQL11433、NAS10445和商品360172.18存储网保持，不借用或重建。
- 目标已安装新Runtime helper与唯一goods root审批补充网络记录，profile及九release不变，其他八应用无新增网络审批记录。helper安装LF SHA为 `df94f72cccafc9bd336eaf83063d8000b923d75b87746f8be1b5e895724fda00`；发布SDK安装LF仍为 `ad5cd66f8f32a387ccfef318cd949d28a6842cf975fa6c1e46437ff5941fd7bd`。

实际回执位于本机SaaS工作区 `audit-2026-10-25/alphabet-server-consolidation/`：`source-final-copy-progress-01.json`、`platform-migration-contract-comparison.actual.json`、`dns-hk48-cutover.confirmed-ui-result.json`、`target-persistent-network-runtime-installed.actual.json`、`http-bridge/canonical-three-rounds-accepted.actual.json`。这是运行与界面实际证据，不是Skill发布凭据，也不在公开仓库携带数据清单、秘密或访问档案。

## 代码、版本与文档验证

Runtime网络源95独立隔离CI通过65项（11新网络、23主机切换/恢复、2主网兼容、29 SDK/origin）及官方quick_validate。最终 `6614266fecd602629b4ecb75bdcbc82f5c20311f` 只改新测试imports，所有其他文件字节、测试功能AST不变；最终Ruff按core CI的Python3.10 target通过。实际隔离解释器为3.12.14，并未声称final661重跑65项或等同GitHub正式check。完整报告 `network-attachments-ci-evidence/independent-network-attachments-review-and-tests.json` SHA `b5edf1dcf5bbb485da44f634094d053e9fe9777bc4bb7002126d6c35ab29e94d`。

本次仅更新core region/direct、三公司交接与本次TASKS/交接记录；helper、SDK、Schema、模板、catalog选择器、版本和NAS设备脚本均不改。版本保持core1.1.44、goods1.0.3、SQL1.1.3、NAS1.0.4；legacy1.2.0和共享交接1.0.0保持。目标01/47.97选择goods/SQL/NAS；48/101选择goods/NAS仅用于历史与观察，不授权恢复源业务。

本次文档的metadata/selectors、本地链接及四个Skill官方quick_validate结果由同任务独立检查记录；旧3ee版本4项与草稿包证据保留，不能替代正式bundle46的公开下载、无缓存resolve或两账号升级验收。

## final_acceptance（Root据真实回执逐项收口）

| 字段 | 当前实际状态 | 需记录的最终证明 |
| --- | --- | --- |
| `main_data_runtime_dns` | passed | 上述最终流、九应用比较与RAM UI保存 |
| `http_canonical` | passed | 三轮6/6宿主机与真实容器同内容；单活、无公网18849 |
| `native_backup_all` | pending | 九应用完整归档、摘要、原服务恢复，不能只看退出码 |
| `restore` | pending | 从实际归档恢复至获授权隔离目标并验证数据/文件；不覆盖线上 |
| `offsite_sftp_windows_ack` | pending | SFTP配置落地/安装收据修复；首次八文件导出、Windows实际下载SHA及服务端受限ACK仍需验收 |
| `target_letsencrypt_renewal` | pending | 目标正规LE lineage、旧origin TLS切换与续期证明；临时PEM不是续期 |
| `employee_browser_mobile` | 本轮未验收 | 获权/拒绝员工真实流程与手机真机；本轮无前端改造 |
| `public_bundle_and_personal_sync` | 待Root发布验收 | clean merged main、bundle46十资产、匿名更新器与无缓存resolve、两账号限定范围同步 |

主接管、单活HTTP取数与未完成的独立项分别报告。源数据和历史在观察/恢复验证完成前不删；NAS旧设备连接最终回收也不能由Runtime48 inactive推定。Root独占后续生产、GH、稳定发布及个人Skill写入。
