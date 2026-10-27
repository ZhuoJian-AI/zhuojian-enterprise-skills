# 当前任务

- [ ] **ALPHABET-OFFSITE-DR-20261027** (@backup_placement_review)：在 `codex/alphabet-offsite-dr-20261027` 独立工作树实现并验证九应用不中断线上备份、企业前缀机外副本、OSS附件覆盖与隔离恢复证据；保留既有Windows链和所有业务权限。只改备份辅助代码、测试和本任务交接，通用Skill规范与版本发布由Root串行负责；接口/容量对齐前不部署。

- [x] **ENTERPRISE-LOCAL-INTEGRATION-20261026 已发布、双账号同步并修复企业现场** (@codex-root)：PR98/main `120a2254`，PR/main CI 940通过/77跳过/1warning；core1.1.49/bundle52/Release423937379于15:02:05CST发布。11匿名资产、4latest、15selectors、原updater新装/48升级/CURRENT及legacy入口通过；两账号18路径备份/CAS限定同步及CURRENT49通过。161 Runtime投影于15:03:32安装，真实CLI与SaaS原始14项features完全一致，doctor与9业务健康通过，配置/容器未变；9仓库12活动工作树16文档已Git备份及FF修正。独立三系统流程评估通过；具体产品尺寸业务服务与真实页面验收仍由企业AI接续，未宣称已打通。见[最终交接](docs/handoff/2026-10-26_enterprise-local-integration.md#正式发布与安装结果)。

- [x] **SHARED-OSS-VALIDATOR-20261025 已发布并双账号同步** (@codex-root)：PR95/main `e0d048b8`，PR/main CI均840通过/77跳过/1 warning，Windows/Linux定向各21通过。core1.1.47/bundle50、Release423318318于18:21:19 CST公开；十匿名资产、四latest、八selector、原updater新装/46升级/CURRENT及legacy入口通过。两账号各5路径备份/CAS同步、范围外保持及CURRENT47已核；未部署Runtime、改云权限或迁移文件。见[最终交接](docs/handoff/2026-10-25_shared-oss-validator.md#正式发布与同步结果)。

- [x] **GATEWAY-RUNTIME-PROFILE-COMPAT-20261025 已随 Skill 发布并同步，企业网关未安装** (@fix_platform_self_service)：旧 0640/0644 非敏感 Runtime metadata 兼容修复随 PR93/main `343d578`、core1.1.46/bundle49 交付；真实 OSS 凭据仍要求 0600。Linux 增量及正式 CI 通过，不修改企业档案或部署网关。见[本轮发布交接](docs/handoff/2026-10-25_multi-owner-self-service.md#实际发布与个人同步)。

- [x] **MULTI-OWNER-SELF-SERVICE-20261025 Skill 已发布并双账号同步** (@codex-root)：PR93/main `343d578`，PR/main CI 均823通过/77跳过/1 warning；core1.1.46/bundle49、Release423304103于17:57:14 CST公开。十匿名资产、四latest、八selector、原updater新装/45升级/CURRENT及legacy入口通过；两账号各39路径备份/CAS同步、范围外保持及CURRENT已核。SaaS PR669在25检查SUCCESS、2跳过后合并为 `44752317`，未部署；企业安装与业务验收另记。见[本轮交接](docs/handoff/2026-10-25_multi-owner-self-service.md)。
- [x] **MULTI-OWNER-RUNTIME-20261025 已随 Skill 稳定分发，企业 helper 未安装** (@fix_runtime_reliability)：冻结 Git 构建、精确提交/运行基线 CAS、源码 refs、v2 Git/数据/配置备份及维护恢复已合入 PR93，随core1.1.46公开并同步个人账号。隔离验证不代替企业服务器安装、真实数据库恢复或业务验收。见[实现交接](docs/handoff/2026-10-25_multi-owner-runtime-reliability.md)及[发布结果](docs/handoff/2026-10-25_multi-owner-self-service.md#实际发布与个人同步)。
- [x] **MULTI-OWNER-SHARED-STORAGE-20261025 已随 Skill 稳定分发，云端未迁移** (@fix_storage_inventory)：共享业务/备份桶企业前缀、旧布局兼容、机外备份发现/完整读回及隔离恢复工具已合入 PR93，随core1.1.46公开并同步；未创建/变更云 IAM、bucket，未迁移既有文件或删除恢复点。见[本轮边界](docs/handoff/2026-10-25_multi-owner-self-service.md#尚未上线的运行时范围)。

- [x] **MULTI-SYSTEM-INTEGRATION-20261025 已发布并双账号同步** (@codex-root)：core1.1.45整体确认、精确拆分、依赖恢复和整链验收随PR91合入217ddca；PR/main CI均729通过/57跳过。bundle-v1.4.48/Release423165869于13:25:58 CST公开，十匿名资产、四latest、八selector、core新装/44升级/CURRENT及legacy入口全部通过；两账号各六路径备份/CAS同步及范围外保持已核。沿用现有API/2.4/2.5，其他五Skill原包保持；没有SaaS/Runtime/业务部署。见[实际交接](docs/handoff/2026-10-25_multi-system-integration.md#实际发布与同步结果)。

- [x] **ALPHABET-SOURCE-RETIREMENT-20261025 已退役、发布并同步** (@retirement_docs)：源101已退订释放，124历史文件机外SHA覆盖、NAS旧分支撤除、目标9health/4共享通过。SQL1.1.4/goods1.0.4/NAS1.0.5与旧selector撤销随PR89/main41fb1ca合入；bundle47/Release423153399于12:48:06 CST公开，匿名十资产/四latest/八selector/三公司fresh-CURRENT全部通过。两账号各13路径备份/CAS同步与范围外保持已核，core1.1.44及另两ZIP字节不变。details12:42及billing12:45自然刷新、Console9台/旧源0通过；费用原DeepSeek partial边界保留。见[交接](docs/handoff/2026-10-25_alphabet-source-retirement.md)。

- [x] **ROOT-APPROVED-NETWORK-ATTACHMENTS-20261025 已发布并同步**：helper df94/唯一goods审批记录已在目标安装，九原镜像health200；core1.1.44/bundle46已从main bc455公开，原生CI、独立65项与公开升级/匹配检查通过。双账号各12个core路径限定同步、范围外保持；见[实际交接](docs/handoff/2026-10-25_alphabet-consolidation-actual.md#公开发布与个人同步实际终态)。

- [x] **ALPHABET-RUNTIME-ORIGIN-ADOPTION-20261025 主机与分发交付完成**：源两项目归入47/01，原数据/身份/权限/网址保留；九备份、两库隔离恢复/全归档校验、Windows八SHA/受限ACK、正规LE/两renew dry-run、九health及源单活均通过。bundle46公开10资产、latest4、三更新路径/CURRENT和六resolver通过；四Skill×两账号各25路径同步完成。部署台账PR114/main55与两账号授权delta同步、私人分析入口四文件同步及codex02 shops885实查完成；源原件未删除，用户业务/真机未测。见[实际交接](docs/handoff/2026-10-25_alphabet-consolidation-actual.md#公开发布与个人同步实际终态)。

- [ ] **SAME-COMPANY-MODULE-REUSE-20261024**（@skill_process_audit，core1.1.43文档补充）：默认同一家公司、单服务器、多业务负责人复用现有应用/模块与权威服务；Codex业务确认一次，AI使用既有Runtime调用获权API。独立审查、34项受影响检查、quick_validate及CLI原始摘要/版本保持核对通过；待正式PR CI/root合并后重新冻结bundle-v1.4.45候选。仅文字更正，不实现多企业共用主机、个人凭据或实际迁移；未发布、个人同步或修改生产。见docs/handoff/2026-10-24_same-company-module-reuse.md。

- [ ] **CODEX-RUNTIME-INTEGRATION-CONFIRMATION-20261024**（@skill_process_audit，core1.1.43候选）：Codex业务澄清/复用选型、逐端本机确认/撤销、requester应用及未知只GET核实已实现；Windows27项、公司CI完整core709通过/58跳过及真实CLI↔API/PG联合11命令通过。保持2.4/2.5，不汇集key、不改业务角色；待正式PR CI/root审阅、合并与分发决策。本轮未发布Release、安装个人Skill或部署SaaS/子系统。交接：docs/handoff/2026-10-24_codex-runtime-confirmation.md。

- [ ] **SAAS-ENTERPRISE-GATEWAY-CONTRACT-20261023** (@codex-gateway-acceptance)：仅对齐核心参考的 SaaS UUID 生命周期／加密 DB 来源／身份鉴权边界；patch1.1.41，正常 PR/CI 后从干净合并 main 构建新稳定 bundle。保留其他 Skill 内容、2.4／2.5及既有本机差异，不重发 Runtime 或业务系统；公开资产和两账号必要元数据同步分别核验。

- [ ] **ZHUOJIAN-SHARED-RUNTIME-20261022** (@codex-root)：企业 Runtime 身份已登记，主机适配/备份/双应用验收 pending。新增窄选择器企业交接草稿，待 reviewed PR、稳定 Release 及无缓存 runtime/host 解析；不能报告完整初始化或原生 Lab 上线。核心 Skill/安装器未修改。

- [x] **PLATFORM-PROJECT-REGISTRATION-20261016 已发布并双账号同步**（@codex-root）：PR70/main `b4bb1b6`、PR/main CI通过；core1.1.34 / bundle-v1.4.35已发布，九资产匿名SHA、原更新器新装/隔离升级/CURRENT通过。两个账号各6项Builder及5项部署Skill授权更新SHA一致，原有非范围文件保留；实际账号均CURRENT1.1.34。企业子系统归所属企业，独立项目归平台项目清单，强制域名/管理入口实点及原站兼容。未部署任何运行时。见[交接](docs/handoff/2026-10-16_platform-project-registration.md)。

- [x] **SHARED-MODEL-CATALOG-20261016**（@codex-shared-gateway）：PR68/main `6622588`、main CI `38851040609`成功；1.1.33 / bundle-v1.4.34正式发布，九资产匿名hash、原更新器新装/CURRENT与隔离1.1.32升级通过；双账号备份后各5指定文件与公开包一致、CURRENT1.1.33，无关内容保持。未改Runtime/Schema/模板或其他Skill，旧学院和业务服务未发布；见shared-model-catalog-contract正式发布补充。

- [x] **BUILDER-GATEWAY-SCOPE-REVERT-20261008 源码修正**（@codex-builder-gateway，唯一回退写入者）：用户纠正本轮只修改“灼见服务器部署”Skill；精确撤回误纳入 Builder 的 PR #64 / merge `e8ecda8`，保留其他历史变更。基于当时最新 `origin/main` 新工作树执行 `git revert --no-commit -m 1 e8ecda8`，Builder 包内容与第一父提交 `539d060` 相同、版本恢复1.1.30；完整核心522 passed/53 skipped/1 warning、quick_validate通过，PR合并待完成。公开稳定通道及两账号均仍1.1.30，两处156个包文件全部匹配；codex02另有4个既存pycache未清理。无Release/tag发布、无安装修改，本地未发行资产仅保留。见 `docs/handoff/2026-10-08_builder-gateway-scope-revert.md`。

- [x] **AI-BUSINESS-ACCEPTANCE-20261001 稳定规范已发布**（@codex-remediation-files，version/release single-flight）：core 1.1.29 / bundle-v1.4.30 于 2026-10-01 22:32:29 CST 从 PR #60 / `a7caac9b` 发布。真实完成、持久化/流式、文件版本回执与视觉覆盖、上下文、历史来源/关系、冷热首屏及撤权增量验收已同步；不限制模型业务答案或工具顺序。干净合并源码 522 passed / 53 skipped、PR/main CI、九匿名资产摘要、原始更新器新装/本机 1.1.28→1.1.29/CURRENT、两处 156 文件逐字节匹配通过；其他四个 Skill ZIP 不变。2.4/2.5、权限/DLP/人工操作保持，本次没有 SaaS、Runtime 或子系统部署，不关闭未测业务/图片理解问题。见 [正式发布证据](docs/handoff/2026-10-01_business-ai-acceptance-release.md)。


- [x] **ASSISTANT-CHROME-THEME-20260923 已发布**（@codex）：core 1.1.21 经 PR #39 / `37cffdb` 合并并公开发布 `bundle-v1.4.21`；423 passed／41 skipped、CI、九资产 SHA-256、公开全新安装／CURRENT 与本机 1.1.20→1.1.21 均通过，安装传输使用临时 curl 以绕过本机 Python urllib／代理断流。SaaS 前端已先行受控部署；四个业务子系统未改、未部署。见 [稳定发布补充](docs/handoff/2026-09-23_assistant-chrome-theme-contract.md#稳定发布补充2026-09-23以本节状态为准)。

- [x] **ADAPTIVE-SUBSYSTEM-SHELL-THEME-RELEASE-20260922**（@codex）：SaaS source `9f104d5` / manifest `3cbe964` 已于 21:39:17 CST 受保护发布并通过九服务健康、真实张三桌面／李四手机双系统验收；Skill PR #37 / `f429ee1` 已合并，core 1.1.20 / `bundle-v1.4.20` 于 21:54:36 CST 发布。CI 成功，本地 423 passed／41 skipped；九资产摘要、公开新装／CURRENT／1.1.19 升级及本机 1.1.20 安装通过。保持 2.4／2.5 与四字段 Schema 不变；现有主题登记正确的子系统未改业务代码、未重新部署。见 [发布交接](docs/handoff/2026-09-22_adaptive-shell-theme-contract.md#稳定发布补充2026-09-22)。

- [x] **ASSISTANT-WORKFLOW-RELEASE-20260922**（@codex）：SaaS source `8983e5b` / manifest `aa5a9a7` 于 19:22:59 CST 受保护部署完成、九服务 healthy 后，PR #35 / `6eba784` 的 core 1.1.19 / bundle-v1.4.19 于 19:31:19 CST 发布。CI 422 passed / 41 skipped，9 资产摘要一致、其余4包不变。公开默认新装及 CURRENT 通过；旧升级、兼容迁移与本机安装在 urllib 连接中断后经临时 curl 传输桥和原更新器全部校验完成，不把默认网络失败算通过。合并收尾以下早期候选的发布待办；不部署子系统或 Runtime helper，见 [发布补充](docs/handoff/2026-09-22_1657_assistant-workflow-guidance-skill.md#稳定发布补充2026-09-22)。

- [ ] **ASSISTANT-WORKFLOW-GUIDANCE-20260922 下游真实流程验收**：企业文化、生产协同、商品动销负责人用已发布 Skill 1.1.19 梳理真实流程、证据与检查 Action，按需适配并分别发布；核验员工权限/数据范围、失败与无异常分离、版本冲突、停用/撤权、建议进入唯一助手草稿及确认/拒绝，补手机真机。必要 Runtime helper 受控更新亦由实际目标任务安排。本轮未修改业务服务器，生产协同款号错配未修复，不承诺后台监控或自动写入。见 [交接](docs/handoff/2026-09-22_1657_assistant-workflow-guidance-skill.md)。

- [x] **ASSISTANT-PAGE-SUGGESTIONS-20260922 发布**：随 core 1.1.19 发布；历史测试保留于 [交接](docs/handoff/2026-09-22_1519_page-suggestions-skill.md)，真实业务接入合并至上方下游验收待办。

- [x] **BUSINESS-IDENTITY-REVIEW-20260922 规范发布**：随 core 1.1.19 发布；不代表历史误归档排查或业务修复完成。历史依据见 [交接](docs/handoff/2026-09-22_1437_business-identity-review.md)，实际取证/修复由生产协同负责人另行执行。

- [x] **ASSISTANT-OPEN-BRIDGE-20260922 发布**：PR #35 已合并，随 core 1.1.19 发布；真实入口与必要 helper 更新合并至上方下游待办。历史依据见 [入口交接](docs/handoff/2026-09-22_assistant-entry-bridge.md) 与 [Runtime 交接](docs/handoff/2026-09-22_runtime-platform-capabilities.md)。

- [x] **MOBILE-NAV-PREFERENCE-20260920** (@codex)：PR #29 合并为 `d1f5c65`，core 1.1.16 / bundle-v1.4.16 已发布；244 passed、41 skipped，公开安装、本机正式更新器 1.1.15→1.1.16 通过。SaaS 默认展开、显式收放及跨窗口偏好已上线，三个子系统登记已核对，无需业务 ECS 部署。见同日 mobile-navigation-preference 交接。

- [x] **ASSISTANT-PRESENCE-ANCHORS-20260920 本地候选** (@codex)：跨域子系统内部 AI 光标已升级为强制语义锚点契约；新增 `assistant-presence.v1` 能力协商、Manifest 锚点登记、模板适配器、源码校验与验收规则。保持 `contractRevision=2.5`，不开放父页面 DOM/CSS/任意选择器，不自动扩权或替代 SaaS/子系统运行时发布。核心 183 passed、1 skipped，兼容入口 18 passed，两个 Skill 快速校验通过；尚未合并或发布稳定包。
- [x] **ASSISTANT-PRESENCE-ANCHORS-20260920 稳定发布** (@codex)：PR #27 已合并为 `addf319`，`bundle-v1.4.14` 与 core 1.1.14 已发布，公开更新器验证通过；三个下游子系统的运行时同步另行验收。
- [ ] **ASSISTANT-PRESENCE-VIEWPORT-20260920** (@codex)：修复手机窄屏/超高锚点下轨迹边框和短标签越出 iframe 视口的问题，发布 core 1.1.15 / `bundle-v1.4.15`，再回灌企业文化、生产协同和商品动销并完成 Runtime 验收。

- [x] **NAVIGATION-THEME-REQUIRED-20260918** (@codex-nav-theme)：模块导航主题已升级为 core 1.1.11 的发布必检项，并随 `bundle-v1.4.11` 稳定发布；脚手架、Schema、源码、端点、Runtime 发布及旧系统手工登记均覆盖。241 passed、41 skipped；公开下载与本机正式更新器已验证。既有 SaaS 版本兼容运行，三个业务子系统仍待各自负责人适配、部署与验收。见 `docs/handoff/2026-09-18_required-navigation-theme.md`。

- [x] **NAVIGATION-THEME-20260917** (@codex)：可选受控模块导航主题已随 core 1.1.10 / `bundle-v1.4.10` 发布，公开 Release 与本机正式更新器升级均已验证。只允许四个颜色令牌，不开放任意 CSS，不改变契约版本，也不自动修改或部署业务子系统。见 `docs/handoff/2026-09-17_navigation-theme.md`。

- [ ] 下游真实草稿检查：core 1.1.9 / bundle-v1.4.9 已发布并验证公开安装/自动更新；业务负责人仍需适配、测试及部署子系统。见 `docs/handoff/2026-09-17_mobile-grid-guard.md`。

标准导航已发布 core 1.1.8 / bundle-v1.4.8；本轮任务释放，验收证据与下游待办见 `docs/handoff/2026-09-17_standard-navigation.md`。

- [x] MOBILE-ACCEPTANCE-20260917 (@codex-mobile)：消除手机需求矛盾，明确真实页面验收与未测状态；用户追加授权后发布 core 1.1.7 / bundle-v1.4.7。
  - 229 passed、41 skipped，quick_validate 与自动更新路径通过。浏览器脚本保存在 SaaS 仓库，尚未移植成通用 Skill 工具；未部署业务子系统，未完成真机验收。详见 `docs/mobile-acceptance-20260917.md`。
