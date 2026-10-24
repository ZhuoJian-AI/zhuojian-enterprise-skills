# 同企业服务器归并 Skill44：候选交接，迁移尚未完成

本页记录本地准备状态。core1.1.44及三份公司交接拟随下一个未占用的bundle-v1.4.46发布；当前没有创建或发布该Release、同步个人Skill，也不将初始复制或镜像接收称为实际接管。SaaS实际新能力、源Runtime停用、最终一致DB/文件增量、DNS、员工及backup-all验收完成后，Root再据真实回执收口并发布。

## 分层与版本

| Skill | 本次候选 | 范围 |
| --- | --- | --- |
| zhuojian-subsystem-builder | 1.1.44 | 已初始化目标的同企业归并、实际SaaS cap/module证明、逐应用root0600旧origin记录、原健康commit接管、普通后续发布和backup-all；2.4/2.5与Schema/模板保持 |
| alphabet-goods-dashboard-handover | 1.0.3 | 源/目标与观察状态、原代码/域名/身份/local-managed、HTTP数据与Windows机外备份依赖 |
| alphabet-daoxun-data-bridge | 1.1.3 | 保护目标01既有SQL，区分迁入看板HTTP18849，不改数据口径或写权限 |
| alphabet-nas-data-bridge | 1.0.4 | 保护既有NAS10445/私网代理及共享ACL，不复制第二监听/正文或自动放大应用权限 |

legacy core1.2.0与共享Runtime交接1.0.0及其他范围不改版本；公司IP、域名、任务和私网放在公司交接，未写进core。goods catalog新增目标`aifabei-hk-01`/`47.97.90.161`，保留48/源IP作为当前来源及以后退役观察引导；先读候选状态，不能凭匹配就切换或新建同名应用。SQL/NAS选择器仍按真实既有能力保持。

## Runtime与SDK已经验证的代码

配套源`0a072d834fb0d005007e30523d7e2fa1661d8ddf`在独立公司CI、network-none、只读完整Git归档验证94项通过，含8项新增Runtime/SDK联合、真实API根尾斜杠和普通/采用应用共同backup-all分派；原07268的两项Mock/Path fixture失败保留，产品代码未变。quick_validate通过。本次只补文档、版本及公司候选，不重跑94套、不修改已测两个生产文件：

- Runtime helper `assets/admin-runtime/host/runtime_admin.py` Git原字节SHA `328d782375872b6c102177935f1033c4578d3ef555e4dffa19c02406b26cec8c`。
- 发布SDK `scripts/publish_subsystem.py` Git原字节SHA `ad5cd66f8f32a387ccfef318cd949d28a6842cf975fa6c1e46437ff5941fd7bd`。

实际独立报告位于本机`audit-2026-10-25/alphabet-server-consolidation/runtime-origin-sdk-ci-evidence/independent-runtime-sdk-review-and-tests.json`，旧/新来源和原失败保留；公司最终备份字节、SSO/角色/文件、数据同步及真机仍需现场验收。模拟七普通/一采用应用的backup分派不等于实际目标全应用归档通过。

## 当前迁移边界与后续Root收口

已授权目标是一家公司一台服务器，源101.37的两个项目归并至已有47.97/01；只完成初始约13GB隔离副本和镜像准备，源仍为业务权威。保留目标默认profile、登记key及全部现役应用/网络；原app/release/模块/Action/角色、Git、应用凭据和local-managed键不重建。源两旧hk48域名继续保留，具体端口、单活任务及源观察状态以最终真实登记为准。

Root按实际受限SaaS能力安装并验原helper，保护一致性数据/文件与现有业务，再正常停源Runtime、采用逐应用origin、以原healthy commit登记及GET核原ID/真实requester归属。目标看板拟用回环18849与独立172.29.94.1 relay；SQL11433、NAS10445和Product360的172.18网保持。Windows HTTP隧道、只读SFTP机外备份目标/known_hosts与原E盘保留策略在最终窗口据受审计划切换，不由本草稿改客户端。

完成后记录实际平台源/能力、两个原app UUID及新owner、DB/文件全量摘要、域名/TLS/旧缓存入口、单活同步和完整backup-all/恢复证据、桌面与手机及未测真机，再将三公司环境表由pending改为已接管/退役观察。之后从clean merged main冻结未占用46包，匿名核十资产及更新器；空目录按目标Runtime和host无缓存resolve确获goods/SQL/NAS、无关服务器不误装，最后Root限定同步本次已授权Skill到两账号并核scope外保持。
