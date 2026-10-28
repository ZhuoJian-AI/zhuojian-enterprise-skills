# Runtime 存储预绑定、自动备份接入与首点验收

本轮主责是企业 Runtime 与通用 Skill。SaaS 机器接口、平台管理员 Console/Control、云角色、服务器安装与稳定发布由主任务分别交付；本文件不把源码、测试或 Skill 版本当成线上安装证明。没有操作企业线上、云账号或真实凭据。

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
