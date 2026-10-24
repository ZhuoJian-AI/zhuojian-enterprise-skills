# 当前任务

- [ ] **ROOT-APPROVED-NETWORK-ATTACHMENTS-20261025**（@acceptance_finish，Runtime helper/聚焦测试/接入说明）：从干净 `1c29665014ef7461c118f0380fff93ea6d63aa51` 追加逐应用 root-only 补充内网绑定；部署/回滚停旧版前验证，create/connect/核对后才 start，无记录应用行为保持。本机新11项及原OSS主网1项通过，待独立静审/隔离pytest与quick_validate。SDK、版本44、既有导入脚本保持原字节；Root 独占实际安装、生产、GH、稳定分发及个人同步。见核心Skill `docs/handoff/2026-10-25_root-approved-network-attachments.md`。

- [ ] **ALPHABET-RUNTIME-ORIGIN-ADOPTION-20261025**（@skill_release_finish接文档/版本/公司交接，@acceptance_finish已交Runtime/SDK，Root串行发布）：0a源独立94项通过，产品代码原字节保持；core1.1.44、goods1.0.3/SQL1.1.3/NAS1.0.4及goods目标窄选择器草稿已备，版本4项/四Skill quick_validate/六包元数据及选择器自检通过，未重复94。准备bundle1.4.46；目标同企业归并不重init/覆盖profile，local-managed不自动切OSS。当前只有初副本/镜像准备，实际SaaS能力/源停用/finalsync/DNS/backup-all与用户验收待Root收口，见[候选交接](docs/handoff/2026-10-25_alphabet-server-consolidation-skill.md)。Root独占生产、GH、稳定分发和个人同步，草稿不代表迁移完成。

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
