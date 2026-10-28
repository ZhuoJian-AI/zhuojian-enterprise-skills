# Runtime 存储预绑定、自动备份接入与首点验收

本轮主责是企业 Runtime 与通用 Skill。SaaS 机器接口、平台管理员 Console/Control、云角色、服务器安装与稳定发布由主任务分别交付；本文件不把源码、测试或 Skill 版本当成线上安装证明。未修改企业线上配置、操作云账号或更换真实凭据；后文现场检查均为只读或内存 dry-run。

## 实现范围

- 既有 Runtime 机器身份领取固定平台存储配置与独立业务/备份 STS，严格校验组织 UUID、环境、Runtime、绑定 revision、同地域端点与固定前缀；无云账号/平台 Token 输入，不创建桶或 RAM。
- 备份 `oss2.ProviderAuth` 每次签请求检查并续期。网关只挂载 business-only Unix socket 与专用租约目录，不得到 Runtime key 或备份身份；socket 固定 `GET`、root peer、0700目录/0600节点，稳定目录在 broker 重启时保留。新 STS 上传继承已验私有桶 ACL，不要求 `PutObjectAcl`，旧静态头保持。
- 初始化先在私有暂存目录取得并验证全部租约，所有前置完成后才提交。提交先原子写保持同scope/原凭据路径的 Runtime 元数据，再换租约文件；整个提交在 BaseException 下按原字节/权限 CAS 回退，不覆盖并发未知写入。旧静态身份在元数据已更新而租约尚未替换的窗口仍可用。
- 保留已有 local-managed/OSS release、legacy业务前缀、人工计划/缺失基线和已验收日程。business为null或与现有业务scope不同仅保留旧业务；备份scope或旧凭据路径不同拒隐式接管。内网/公网端点在同bucket/region内保持既有选择。
- 新受保护系统部署落定后自动登记可信计划、排队自己的首次备份/精确云版本回读/隔离恢复。新系统首次登记需当前提交的真实DB、文件、引用及Git证明；旧已上线系统不强制门禁或停服。
- 自动识别实际SQLite魔数、固定挂载、明确DSN/数据库路径和模板附件字段。明确DSN不匹配不退选旧库；PG/MySQL/外部库、未知引用结构、多候选或发现失败逐系统pending，由开发AI补适配，不是交付已保护。
- 在线循环隔离未计划、坏release/数据库等系统，其他旧计划继续并保留旧点。首次任务争锁有界排队；后台凭据续期和安全报告不因正在备份而等待整个数据库作业。
- 平台报告按服务器返回的权威 applicationSlugs、revision与有界point schema上报；尚未平台注册的新本地点保留本机。计划covered与真实最近任务/恢复点分开，不上传云位置、对象键、密钥或正文。

## 安装前置与固定入口

平台先发布机器接口并完成已授权云profile/binding验证。主机只更新本轮受影响的 `runtime_admin.py` 与 `runtime_backup_plan.py`，保持原Runtime key、身份、配置和业务容器；不重跑整机初始化。随附 `install_runtime_backup.py` 安装新bootstrap/online/OSS/evidence CLI与私有venv，然后运行固定初始化入口。

新企业默认 `zhuojian-storage-bootstrap configure`。既有已验收在线计划使用 `configure --preserve-existing-schedule --existing-backup-timer <现场读回的unit>`，不得覆盖旧日程或重复启动全量链。business启用的新网关另需更新本轮网关资产、目录/socket挂载并完成真实隔离与重启探针，再设置未来系统默认；Alpha business:null不要求重发九业务容器。

主机运行时测试须另核实际SDK签名跨过STS到期后成功、新系统自己的首点及门禁、两系统并行和坏库隔离、机器报告归属及管理员桌面/手机入口。原主机恢复、整机启动、生产切回、外部NAS/ERP原件继续各自验收。

## 已运行本地验证

- Windows核心完整检查中间候选：984 passed / 78 skipped / 1 warning（69.54秒）；后续修改另跑受影响测试，不能用这个计数替代最终候选。
- Windows本轮受影响检查在事务/锁复核前：192 passed / 19 skipped / 1 warning；最终候选复测结果后补。
- WSL `ZhuoJian-CI-Trial` 私有venv `/tmp/zj-storage-bootstrap-20261028`；系统Python缺ensurepip/pip，用已授权本地官方pip wheel引导到私有venv，国内镜像安装测试依赖及模板原requirements，无系统包修改。源码经二进制tar传到任务专属 `/tmp/zj-storage-bootstrap-tests-20261028/source`，不假设Windows盘挂载。
- POSIX受影响套件中间候选205 passed / 1 warning，含真实root flock、Unix socket和安装事务；最终候选复测结果后补。
- Linux完整检查第一次因私有venv缺PyJWT导致generated-native子测试失败，997通过/64跳过；补装原模板requirements后，该未修改的生成模板路由测试出现后台线程/锁调用次数失败并挂起。只中断并终止已核对PID、命令和cwd的本任务子pytest（SIGINT未结束后SIGTERM，退出-15），其余997通过/64跳过/205 subtests。未称完整Linux通过，也未修改原模板规避；正式CI仍须通过。

## 发布边界

### 最终逻辑候选的本地结果

功能提交 `f7676a8` 与锁包装修复 `e04b099` 已推送，Draft PR104。e04b099 的 Windows 核心全套 **993 passed / 80 skipped / 1 warning，48.37秒**；同源 WSL root 受影响套件 **212 passed / 1 warning，6.96秒**，包括真实Unix peer/socket和flock争锁排队。Skill quick_validate通过。版本常量原断言50已同步51；初版有界锁未识别旧工具包装的BlockingIOError由实际POSIX测试抓到并修复，失败未抹除。正式CI与独立只读复核继续，尚未合并或发布。

core候选1.1.51保持接入契约2.4/2.5。稳定Release、双账号限定同步、正式PR/main CI及现场安装由主任务另留回执。此处不宣称已发Release、已接入新企业或全部数据库适配完成。

## 正式 PR CI 与现场固定链兼容

PR104 已 Ready。原 head `e3fef773` 对应合成 merge `b57b9bc16e6a6deda0a9281c943c0888e1fe9298` 的正式 GitHub Windows CI run `40615596124` / job `122577225819` 成功：993 passed / 80 skipped / 1 warning（69.73秒），独立 maintenance 5 passed / 1 skipped。旧 skipped run 不计为通过。后续兼容适配另须验新 head，不将上述结果冒充新源码 CI。

2026-10-28 只读核实 Alphabet 机器 `24b1027fbbb34fe080910773ec63ebc9`：自然日程仍是 `zhuojian-online-backup.timer`，03:15 加 15 分钟随机；timer SHA `ce0f86bd09b1830a33d393e4d95133508efcad8d0f8cd0ebc4f830874d0d4f89`，service SHA `e4a3c0ef98d58cfdec6e1463b15f906b58f4d75c963a1fe2477a25446c1d75ed`。原 wrapper 实际指向 `a6de832052f14ef3417b0575ed366c8a3c9553a0941eaab716c5e90d627221ab` 私有工具代；该 SDK 没有 STS provider。旧 ExecStartPre 不仅固定 wrappers/modules，还固定原 23,776字节 plan 的整文件 hash 和九项数量。新的 enroll 默认 JSON 序列化就会改变这个 hash，不能在未适配前运行 configure。

专项维护候选 `scripts/maintenance/upgrade_alphabet_storage_bootstrap_20261028.py` 固定该机器、原 service/timer、旧 preflight/pins 与原九项手工计划。先安装兼容 preflight，仍允许完整旧静态工具代运行；工具切换必须整代吻合，混合或任意源码拒绝。`platform-sts-v1` 凭据仅允许新版 provider 整代，包含实际 daily CLI、备份/续期/计划模块及 Runtime helper。计划验收改为身份及原九项逐项 canonical hash，允许同一 root helper 创建的受限 SQLite 或 pending 追加项；原数据库路径、私有恢复文件和服装历史基线保持。原 Windows 次级导出容量预算与 5GiB 主备份底线按原代码保留。

固定新版工具代为 `7ec8fd487f3f5dc870515f4a44cff5626b4fe9884d0ccd9baa76fa72b40a6632`，源于本候选原样 LF 文件。维护脚本默认 dry-run，`--apply` 仅在全局 Runtime 锁下更新该私有 preflight/pins，提前将原文件及原计划字节保存到其 `before-storage-bootstrap-v1/`，任何取消按原字节与模式 CAS 回退；不读取或更换云凭据，不操作 timer、业务服务或实际备份。原快照已存在、目标有漂移或任务正在运行时拒绝盲目重试。

专项新增/旧 maintenance 在 Windows 22 passed / 2 skipped，WSL root 24 passed，包含实际私有文件和独立生成 preflight 子进程。新增 pending 不阻旧项、旧项变更/越界/非审核字段拒绝、旧 SDK 搭配 STS 拒绝、重命名前后中断回退及保留并发未知写入均已验。Alpha 无落文件 dry-run及新生成 preflight 的实际原静态代内存执行均通过；没有 apply、凭据切换或日程变更。新 preflight SHA `122fc681b9268f2ef669931abc2316e9bc269b809f8bf6a5cd848e393b8b5339`、新 pins SHA `206e59e9fc532bef913923d2a00f3eed6b54972f5118461592f32dc15f578f45`。独立代理重新从现场计算原四文件 SHA、九项及身份 canonical hash，并从 Git LF 字节重新计算新整代/module/helper pins，全部匹配；没有剩余阻断项。

### Alphabet 接管与 daily 回退次序

1. 平台接口/profile/绑定先通过。等待已有备份完成；在 root 私有目录保存原 `runtime.json`、`backup-oss.env`、Runtime helpers 和三个 daily wrappers 的字节/模式/hash，确认旧工具代仍保留。秘密不输出、不上 CI。
2. 从同一审查源码执行上述维护脚本 dry-run、`--apply`。此时原静态 daily 仍应通过新 preflight。只复制本轮两个 host helper，再运行原 `install_runtime_backup.py` 安装新私有 SDK/四个 CLI；运行实际 `ExecStartPre`，确认全部新 pins，仍不换凭据。
3. 执行 `zhuojian-storage-bootstrap configure --preserve-existing-schedule --existing-backup-timer zhuojian-online-backup.timer`。Alpha 的 business:null 保留旧业务 OSS。再次运行实际 preflight、核实原 timer/service 字节和原九项计划 canonical hash，然后运行真正 daily CLI 的机外回读/隔离恢复及跨 STS 有效期验证，才能宣称接管。
4. 如需回退：先核实未知备份结果，等待任务退出；仅暂停本轮 refresh/lease 单元并确认没有新 initial-backup 作业，以 Runtime 锁保护配置恢复。先原子恢复原私有 `runtime.json` 和静态 `backup-oss.env`，再恢复原 helpers/三个 wrappers，最后从 `before-storage-bootstrap-v1/` 恢复原 plan 字节及 pins/preflight（只恢复语义相同的原计划或本 helper 的限定追加，其他手工改动拒绝覆盖）。每个写回须检查当前内容属于本次变更，遇其他修改保留并停止。保留新增系统的恢复点和回退前计划记录，新增系统在旧链回退期间明确待补。原静态 SDK 不得搭配已经过期的 STS 文件。
5. 运行原 preflight 和限定 OSS 读取，确认原 daily timer 的启用/等待状态、SHA 与下一次触发；原业务容器身份和启动时间应保持。若为避免临界触发而短暂停 timer，须按其保存状态恢复。没有生产库回写、业务重启、删除恢复点或重新启用旧停写 timer。

本段是候选安装与回退路径，尚未操作现场；正式 Release、双账号同步和主机采用仍由主任务单独留证。

## 正式稳定发布与安装准备回执

以下11:35验收 checkpoint 更新前文候选状态，不代替仍在主任务中的 SaaS/STS 接管。

- PR104 合并为 `ac317a998079349f86f12e1b819982599599a9dd`。精确 PR run `40623379457` 与 main push run `40623929106` 均成功：核心993 passed / 80 skipped / 1 warning；maintenance22 passed / 2 skipped。main job `122604236059` 实际检出的就是合并源。没有重跑无关套件来增加通过数。
- [bundle-v1.4.54](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.54)，Release `426220999`，于2026-10-28 03:10:51 UTC（11:10:51 CST）正式发布，非 draft/prerelease，tag 解析为上述合并源。notes明确 SaaS0089仍在发布流程，预绑定及主机采用另验。
- core1.1.51 ZIP 840,721字节、194项，SHA-256 `35c78320d33553f776fc6011a3227dd99bbb00ef67086374fe1823a276e3f7e6`。每项核对原样 Git LF 字节，SDK 整代准确为 `7ec8fd487f3f5dc870515f4a44cff5626b4fe9884d0ccd9baa76fa72b40a6632`。本机默认 `git archive` 会受 CRLF 转换影响，核对与传输使用单次 `-c core.autocrlf=false` 或该已验 ZIP，不修改全局 Git 配置。六个无关 ZIP及 bootstrap 经源子树/展开内容/元数据核对后保留前版官方原字节。
- 十一项正式资产已无登录完整下载，大小、官方 digest 和本地候选 SHA 全匹配。未修改的公开 updater 使用默认 latest URL完成新装51、50→51升级及各 CURRENT；legacy按自己的 Skill 先 CURRENT1.2.0，再 `install-core` 迁移51。三份 canonical 安装各194项完全一致、零 extras。初次测试的过长审计目录触及 Windows 路径限制，短任务目录的完整复验通过，失败记录保留。
- 两个真实 Windows 账号只写本次25个差异路径，20个旧文件各自先备份、5个新路径记录原不存在，逐文件 CAS及原子替换。原已存在的换行差异保留（分别6与1路径），每账号其余169个公共路径和 extras 均保持原字节或元数据；未覆盖整个 Skill、其他 Skill、凭据或全局规则。两边原 updater 均 `SKILL_UPDATE_CURRENT 1.1.51`。

Alphabet准备安装另有以下真实结果，尚未切换存储身份或启动新备份：

- 现役机器身份保持 `24b1027fbbb34fe080910773ec63ebc9`。准备前识别出其他受控业务发布已完成：inspiration `bdda3a63` 与 product-360 `5a86f0a4`，无 pending、锁空闲；保留这些当前版本，未用更早容器清单冒充本轮前后基线。
- 原 profile、静态 backup env、helpers、wrappers、plan及 pins 已保存在 root-only 私有回退目录，原模式与 hash 有账；凭据没有离开主机或进入仓库。固定维护脚本已 apply，旧静态整代的真实 ExecStartPre先验通过。
- stable54 原样两个 host helper和全套备份 CLI/私有 SDK 已安装，代码 hash及整代均匹配。Alpha 的严格私有 pins 使用 helper0700/planner0600，保留 root 调用能力；未运行整机初始化。实际 daily ExecStartPre通过新版完整 pins，五个 CLI `--help`通过。原静态 `Auth` 对现有备份命名空间的真实列表读取、桶版本控制检查成功，没有写云对象。
- 本轮安装前后11容器的 ID/image/启动时间/重启数/健康状态完全相同，profile、原plan、backup env及业务OSS env均原字节相同，timer/service状态保持，安装后可用7,831,695,360字节。既存非业务容器原有 unhealthy保持，未声称11容器全健康。
- **没有**运行 `configure`、换 STS、安装新定时链、执行新全量备份或生成新恢复点。旧静态日程继续；需等 SaaS0089上线且平台绑定真实 verified 后，再按前述接管步骤完成续期、机外回读与隔离恢复。原服装历史220缺失仍是 partial，不因工具更新变绿。

公开回执不含私有配置或用户正文。详细安全元数据留在本任务 `runtime-release/` 与 `alpha-preparation/`，远端私有回退材料由平台 root管理；机外数据恢复、主机完整重建、生产回写和实体手机验收分别保留原边界。
