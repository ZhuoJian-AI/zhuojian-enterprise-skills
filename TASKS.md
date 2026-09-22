# 当前任务

- [x] **ASSISTANT-RUNTIME-CAPABILITIES-20260922 本地候选** (@codex-integration-boundary)：Runtime 固定端点只读能力发现 CLI 与脱敏/失败回归完成，120 passed / 1 skipped；未安装宿主机、未发布 Skill、未部署 SaaS 或子系统。见 [交接](docs/handoff/2026-09-22_runtime-platform-capabilities.md)。

- [ ] **ASSISTANT-OPEN-BRIDGE-20260922** (@codex)：随 SaaS 候选实现补齐业务目标进入同一助手的可选协商协议、无凭据浏览器适配器及拒绝/超时测试；保持 2.4/2.5、既有业务与后台委托边界。先验证 SaaS 实现，再发布稳定 Skill；本次不接管或部署业务子系统。

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
