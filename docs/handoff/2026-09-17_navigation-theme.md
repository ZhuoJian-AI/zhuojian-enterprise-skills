# 模块导航主题 Skill 发布

日期：2026-09-17；执行：Codex；范围：`zhuojian-subsystem-builder`。

## 结论

core 1.1.10 为 v2.4／v2.5 Manifest 增加可选的 `presentation.moduleNavigationTheme`。它不是 CSS 注入口，只允许四个颜色令牌，并要求普通文字、选中文字和选中标识达到契约规定的对比度。主题缺失或无效时必须使用 SaaS 默认色，不能影响登录、权限、Bridge 或业务页面加载。

Schema、语义校验、正文、迁移参考、平台契约和原生模板说明已同步。Skill 自动更新只更新开发规范，不会自动改写或部署现有业务子系统。

## 验证

- core：233 passed、41 skipped。
- `quick_validate.py`：通过。
- 新增检查覆盖合法主题、任意 CSS 拒绝、错误格式和低对比度拒绝。

## 发布记录

- 源码 PR：[#21](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/pull/21)，合并提交 `7f590687fb8a2da8c62ce6f8af3312bc95510500`。
- 稳定 Release：[`bundle-v1.4.10`](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.10)。
- Release ZIP SHA-256：`2f5cf6d480b3b47952bb9a5bad34213ac30e1df84352cb0e9809ed11006ff8cd`。
- 本机正式更新器验证：`SKILL_UPDATED 1.1.9 -> 1.1.10`。
- 匹配的 SaaS scoped source `50a793b` 与 manifest `c4712fb` 已在 staging 维护发布，真实八模块目录与切换验收通过。

## 下游边界

业务负责人可以在真实子系统中复用自身品牌色，但须完成源码适配、双端测试、部署和 Manifest 同步后再报告生效。没有登记主题的系统继续使用平台默认导航色，不构成升级失败。Skill 自动更新只更新开发规范，不会替业务负责人改写业务仓库、部署 ECS 或同步运行中的 Manifest。

