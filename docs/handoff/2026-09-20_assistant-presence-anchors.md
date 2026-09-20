# 业务助手语义锚点强制契约

日期：2026-09-20；范围：`zhuojian-subsystem-builder`；目标版本：core 1.1.14 / `bundle-v1.4.14`。

## 变更边界

- 每个 v2.5 AI 页面必须登记非空 `interactionAnchors` 和 `defaultInteractionAnchorKey`，并让本页全部 AI Action 恰好映射到一个稳定锚点。
- 业务 DOM 使用同名 `data-zhuojian-anchor`；模板适配器协商 `assistant-presence.v1` 后，仅在子系统自己的 iframe 文档内滚动、定位和绘制不拦截点击的光标与短状态。
- SaaS 只可下发已登记 `anchorKey`，不得下发 CSS 选择器、坐标、DOM、CSS、业务参数或模型原始工具参数。消息必须校验父窗口、Origin、应用、模块、页面和 launch nonce。
- 子系统可以用 `--zhuojian-ai-presence-color` 令牌让光标匹配自身视觉；不得让 SaaS 注入样式。完整文字说明始终保留，光标只是可见辅助。
- 未协商、身份不匹配、锚点不存在或运行旧版本时，必须安全回退平台级状态。Skill 发布不会自动改写、部署或证明现有子系统已同步。

## 模板与校验

- Schema、Manifest 语义检查、源码校验、脚手架与原生模板同步覆盖新契约。
- 模板提供受控适配器、默认真实 DOM 锚点、reduced-motion 和自动隐藏；适配器拒绝额外字段和任意定位输入。
- `contractRevision` 继续为 2.5；登录、权限、Action、文件、可用性和现有导航契约均不改变。

## 验证证据

- `skills/core/zhuojian-subsystem-builder`: 183 passed、1 skipped。
- `skills/core/aifabei-subsystem-builder`: 18 passed。
- `quick_validate.py`：两个 Skill 均为 `Skill is valid!`。
- Node 适配器契约测试由 Python 测试驱动，覆盖 readiness、合法高亮、未知锚点、错误 Origin/nonce、额外字段和清理。

## 发布与下游状态

- 当前仅为本地发布候选，尚未合并 PR、创建 Release 或验证公开更新目录。
- 稳定包必须从合并后的干净 `main` 构建，目标 tag 为 `bundle-v1.4.14`。
- 企业文化、生产协同、商品动销必须分别核对服务器真实 Git 基线后再适配并部署；在运行端点、双端页面和真实业务助手链路验收前，不得报告同步完成。
