# 模块导航主题 Skill 发布

日期：2026-09-17；执行：Codex；范围：`zhuojian-subsystem-builder`。

## 结论

core 1.1.10 为 v2.4／v2.5 Manifest 增加可选的 `presentation.moduleNavigationTheme`。它不是 CSS 注入口，只允许四个颜色令牌，并要求普通文字、选中文字和选中标识达到契约规定的对比度。主题缺失或无效时必须使用 SaaS 默认色，不能影响登录、权限、Bridge 或业务页面加载。

Schema、语义校验、正文、迁移参考、平台契约和原生模板说明已同步。Skill 自动更新只更新开发规范，不会自动改写或部署现有业务子系统。

## 验证

- core：233 passed、41 skipped。
- `quick_validate.py`：通过。
- 新增检查覆盖合法主题、任意 CSS 拒绝、错误格式和低对比度拒绝。

## 下游边界

业务负责人可以在真实子系统中复用自身品牌色，但须完成源码适配、双端测试、部署和 Manifest 同步后再报告生效。没有登记主题的系统继续使用平台默认导航色，不构成升级失败。

