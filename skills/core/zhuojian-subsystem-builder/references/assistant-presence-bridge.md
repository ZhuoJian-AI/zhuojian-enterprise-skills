# 业务助手语义锚点 Bridge

这项能力让用户在保留完整文字说明的同时，看见 AI 正在业务页的哪个区域查询、操作或核验。SaaS 负责编排可信事件和平台级回退；子系统负责登记语义位置并在自己的 iframe 文档内绘制光标。Skill 规定契约和验收，不代替任一端运行时代码或部署。

## Manifest 与业务 DOM

每个 v2.5 AI 页面必须声明非空 `aiSemantics.interactionAnchors` 和 `defaultInteractionAnchorKey`。锚点结构固定为：

```json
{
  "anchorKey": "order_results",
  "name": "订单结果",
  "description": "筛选结果、汇总指标和订单操作区域。",
  "actionKeys": ["orders.query", "orders.export"]
}
```

- `anchorKey` 是页面内稳定语义标识，不是选择器；同页不可重复。
- 每个本页 `aiEnabled` Action 必须恰好出现在一个锚点的 `actionKeys` 中。锚点不能绑定未登记、未启用或其他页面的 Action。
- `defaultInteractionAnchorKey` 必须引用本页锚点，供导航和无更细目标时使用。
- 业务 DOM 用 `data-zhuojian-anchor="order_results"` 标记真实区域。一个页面可登记多个区域，但不得为每行数据生成无界 Manifest 锚点；具体记录仍由文字说明和业务上下文表达。
- 显示名称、DOM 位置、尺寸和颜色由子系统决定。只允许通过子系统自己的 `--zhuojian-ai-presence-color` 等本地样式适配，不把任意 CSS 交给 SaaS。

## 能力协商

平台在可信 `zhuojian:host-ready` 的 `capabilities` 中声明 `assistant-presence.v1`。子系统只有在完成 `source`、`Origin`、应用和启动 nonce 校验后，才返回：

```json
{
  "type": "zhuojian:assistant-presence-ready",
  "version": 1,
  "application_slug": "orders",
  "launch_nonce": "本次启动 nonce",
  "module_key": "orders",
  "page_key": "orders.list",
  "anchor_keys": ["order_results"]
}
```

`anchor_keys` 只能来自当前文档实际存在且列入配置的 `data-zhuojian-anchor`。不能凭 Skill 版本或 Manifest 推断运行中的 iframe 已支持。

## 展示请求与结果

SaaS 仅可向当前可信 iframe 发送已登记且已协商的目标：

```json
{
  "type": "zhuojian:assistant-presence",
  "version": 1,
  "application_slug": "orders",
  "launch_nonce": "本次启动 nonce",
  "request_id": "assistant-request-0001",
  "module_key": "orders",
  "page_key": "orders.list",
  "anchor_key": "order_results",
  "phase": "acting",
  "label": "正在查询订单"
}
```

`phase` 只允许 `navigating | acting | verifying | completed | failed`。消息不得增加 selector、坐标、DOM、HTML、CSS、URL、Token、角色、原始工具参数、模型私有推理或业务记录。子系统重新校验完整身份和字段白名单，在自身文档中查找完全匹配的已登记锚点，绘制 `pointer-events:none` 的只读光标/边框/短标签，并返回同一身份与请求号的 `zhuojian:assistant-presence-result`，状态为 `shown | missing | stale`。

光标不得执行点击、填写或确认，也不能替代真实 Action。写入仍由既有确认、版本、权限、幂等与业务回执控制。完整文字答复、进度文字和失败说明始终保留，视觉痕迹只是辅助。

## 桌面、手机与回退

- 桌面端业务 iframe 继续可见、可操作；助手是伴随关系，不使用遮罩阻断页面。光标只出现在子系统 iframe 内。
- 手机端可以把目标滚动到可视区并短暂展示光标，同时用 SaaS 跟随条保留完整文字进度；遵守 `prefers-reduced-motion`，不强制动画。锚点高于一屏或靠近视口边缘时，边框宽高必须按 `left/top` 之后的剩余视口夹紧，AI 标记和短标签不得伸出 iframe 可视区。
- 未协商、锚点未登记、DOM 缺失、nonce 过期、页面已切换或结果超时时，SaaS 只回退模块/页面级伴随提示，不发送选择器或猜测目标，不把视觉失败说成业务失败。
- 旧 2.4/2.5 运行版本继续可用；本 Skill 的新发布门禁只约束使用新版 Skill 新建或再次发布的 v2.5 AI 页面。现有线上系统必须分别改代码、测试、部署并重新登记，不能只更新 Skill。

## 验收清单

1. Schema、源码和端点校验拒绝缺锚点、重复锚点、跨页 Action、未覆盖 AI Action 或错误默认锚点。
2. 错误 Origin/source/nonce、额外字段、选择器注入、未登记锚点和重放请求不得展示。
3. 合法查询、写入前后核验、导航与失败阶段均保留文字说明；光标不能替代确认或制造成功回执。
4. 桌面和手机验证嵌入页仍可读；手机目标滚动、旋转、软键盘、缩放、减少动态效果和窄屏不裁切关键操作。
5. 不支持能力、旧 iframe、DOM 锚点临时缺失和页面切换都能回退，不弹系统故障、不重载页面、不重试业务写入。
6. 发布状态分别记录：Skill 版本、SaaS 构建与部署、每个子系统源码提交/Runtime 部署/Manifest 生效和真实员工验收。
