# Alphabet 主机归并与 Skill44 实际交接

两业务已在47.97/01完成最终数据、原镜像、SaaS归属、DNS、正式证书与备份机接管，九应用均以原镜像恢复health200。下表分别记录实际备份恢复、机外ACK、续期与未测用户流程；公开Skill发布和个人同步仍由Root另行留证。本文接替[准备交接](2026-10-25_alphabet-server-consolidation-skill.md)中的初副本状态；本次没有新增前端或业务功能，手机真机未测。

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
| `native_backup_all` | passed | 本轮九项native JSON、commit、归档/metadata与一致快照逐项核实，原七归档完整SHA、两迁入大归档复用恢复证明；九原镜像服务恢复 |
| `restore` | passed，限明确范围 | 两实际归档完整SHA、全部成员流校验，数据库家族实际恢复至私有tmpfs，integrity/FK0后清RAM；不等于重新部署全部业务后的用户整轮 |
| `offsite_sftp_windows_ack` | passed | Windows八文件完整SHA、Target原生受限ACK与restore同一manifest15caeb14；06:10:17CST TaskReady/LastResult0，无重复kick或残留。原SYSTEM日程/E历史保持 |
| `target_letsencrypt_renewal` | passed | 两canonical lineage/线上leaf一致、到期2027-01-22，两renew dry-run/hook通过；临时代理已清，常态timer原direct，未来自然续期另观察 |
| `employee_browser_mobile` | 本轮未验收 | 获权/拒绝员工真实流程与手机真机；本轮无前端改造 |
| `public_bundle_and_personal_sync` | 待Root发布验收 | clean merged main、bundle46十资产、匿名更新器与无缓存resolve、两账号限定范围同步 |

九项备份证明为`http-bridge/sftp/nine-native-backups-verified.actual.json`，恢复为`target-new-native-backups-restore-checked.actual.json`，实际机外结果为`http-bridge/windows/verified-backup-progress-02.actual.json`和`http-bridge/sftp/native-backup-after-win-ack.actual.json`，同代manifest为`15caeb14385ab4995c41000c15da5bbcb9b3c608defd441343d2652c2512069f`。实际每个迁入应用只有一个新native恢复点，`pruned=[]`；后续策略保留最新两点/两代导出，并在空间不足或未ACK时暂停整批九应用backup.service，业务继续运行。

正式证书证明为`target-canonical-certificates-staged-continuation.actual.json`及独立`final-target-source-tls-nine-health.actual.json`。保留首生产secondary连接超时、云/宿主80已全网允许及三LE验证200的现场证据；两个staging门通过后才执行一次新生产续程。两renew dry-run的子进程使用临时17977代理，已按原PID/creationtime/command清理；常态原timer无该配置。Windows首次完成收据因CIM导出改变Principal序列化而失败，原生COM完整任务定义证明只有Action路径变化，SYSTEM/ServiceAccount5/Highest1不变，随后只读续程补收据，未重跑替换或重设principal。

在恢复和机外ACK之后，只清目标本轮initial-staging中124个源已保留且逐inode/SHA相等的历史副本，释放11,782,852,455字节，空闲24,260,608,000字节。此前242个初始数据副本也只清目标重复项。源全部历史、Windows历史、正常九应用数据/备份/新导出和其他原件保持；临时复制grant精确撤除，HTTP/ACK/原keys保留。源实例仍留观察，NAS旧设备最终回收不能由Runtime48 inactive推定。Root独占后续GH、稳定发布及个人Skill写入。
