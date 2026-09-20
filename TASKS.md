# 当前任务

- [ ] **MOBILE-NAV-PREFERENCE-20260920** (@codex)：明确移动端平台模块导航默认展开、仅用户主动收放、切换和重入保持用户选择的强制规范；SaaS 主责持久化，子系统只提供稳定登记。发布 core 1.1.16 / bundle-v1.4.16，验收稳定更新器；不改变协议版本或业务模板。

- [x] **ASSISTANT-PRESENCE-ANCHORS-20260920 本地候选** (@codex)：跨域子系统内部 AI 光标已升级为强制语义锚点契约；新增 `assistant-presence.v1` 能力协商、Manifest 锚点登记、模板适配器、源码校验与验收规则。保持 `contractRevision=2.5`，不开放父页面 DOM/CSS/任意选择器，不自动扩权或替代 SaaS/子系统运行时发布。核心 183 passed、1 skipped，兼容入口 18 passed，两个 Skill 快速校验通过；尚未合并或发布稳定包。
- [x] **ASSISTANT-PRESENCE-ANCHORS-20260920 稳定发布** (@codex)：PR #27 已合并为 `addf319`，`bundle-v1.4.14` 与 core 1.1.14 已发布，公开更新器验证通过；三个下游子系统的运行时同步另行验收。
- [ ] **ASSISTANT-PRESENCE-VIEWPORT-20260920** (@codex)：修复手机窄屏/超高锚点下轨迹边框和短标签越出 iframe 视口的问题，发布 core 1.1.15 / `bundle-v1.4.15`，再回灌企业文化、生产协同和商品动销并完成 Runtime 验收。

- [x] **NAVIGATION-THEME-REQUIRED-20260918** (@codex-nav-theme)：模块导航主题已升级为 core 1.1.11 的发布必检项，并随 `bundle-v1.4.11` 稳定发布；脚手架、Schema、源码、端点、Runtime 发布及旧系统手工登记均覆盖。241 passed、41 skipped；公开下载与本机正式更新器已验证。既有 SaaS 版本兼容运行，三个业务子系统仍待各自负责人适配、部署与验收。见 `docs/handoff/2026-09-18_required-navigation-theme.md`。

- [x] **NAVIGATION-THEME-20260917** (@codex)：可选受控模块导航主题已随 core 1.1.10 / `bundle-v1.4.10` 发布，公开 Release 与本机正式更新器升级均已验证。只允许四个颜色令牌，不开放任意 CSS，不改变契约版本，也不自动修改或部署业务子系统。见 `docs/handoff/2026-09-17_navigation-theme.md`。

- [ ] 下游真实草稿检查：core 1.1.9 / bundle-v1.4.9 已发布并验证公开安装/自动更新；业务负责人仍需适配、测试及部署子系统。见 `docs/handoff/2026-09-17_mobile-grid-guard.md`。

标准导航已发布 core 1.1.8 / bundle-v1.4.8；本轮任务释放，验收证据与下游待办见 `docs/handoff/2026-09-17_standard-navigation.md`。

- [x] MOBILE-ACCEPTANCE-20260917 (@codex-mobile)：消除手机需求矛盾，明确真实页面验收与未测状态；用户追加授权后发布 core 1.1.7 / bundle-v1.4.7。
  - 229 passed、41 skipped，quick_validate 与自动更新路径通过。浏览器脚本保存在 SaaS 仓库，尚未移植成通用 Skill 工具；未部署业务子系统，未完成真机验收。详见 `docs/mobile-acceptance-20260917.md`。
