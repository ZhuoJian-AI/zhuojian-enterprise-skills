# 当前任务

- [ ] **NAVIGATION-THEME-REQUIRED-20260918** (@codex-nav-theme)：将模块导航主题从可选展示增强提升为 Skill 发布必检项。验收：新脚手架生成有效主题；源码、端点和登记前缺失/无效主题拒绝通过；既有已登记系统不因 Skill 更新被 SaaS 停用；测试、稳定 Release 和公开更新路径有证据。

- [x] **NAVIGATION-THEME-20260917** (@codex)：可选受控模块导航主题已随 core 1.1.10 / `bundle-v1.4.10` 发布，公开 Release 与本机正式更新器升级均已验证。只允许四个颜色令牌，不开放任意 CSS，不改变契约版本，也不自动修改或部署业务子系统。见 `docs/handoff/2026-09-17_navigation-theme.md`。

- [ ] 下游真实草稿检查：core 1.1.9 / bundle-v1.4.9 已发布并验证公开安装/自动更新；业务负责人仍需适配、测试及部署子系统。见 `docs/handoff/2026-09-17_mobile-grid-guard.md`。

标准导航已发布 core 1.1.8 / bundle-v1.4.8；本轮任务释放，验收证据与下游待办见 `docs/handoff/2026-09-17_standard-navigation.md`。

- [x] MOBILE-ACCEPTANCE-20260917 (@codex-mobile)：消除手机需求矛盾，明确真实页面验收与未测状态；用户追加授权后发布 core 1.1.7 / bundle-v1.4.7。
  - 229 passed、41 skipped，quick_validate 与自动更新路径通过。浏览器脚本保存在 SaaS 仓库，尚未移植成通用 Skill 工具；未部署业务子系统，未完成真机验收。详见 `docs/mobile-acceptance-20260917.md`。
