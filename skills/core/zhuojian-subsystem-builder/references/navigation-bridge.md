# 标准模块与页面导航

适用于同一应用内的页面按钮、模块切换及独立入口。SaaS 与子系统可位于不同服务器，不需要共享文件系统或服务器账号。SaaS 提供身份、有效目录、重新授权与导航；子系统提供业务页面、数据及业务校验。隐藏重复导航不等于禁止页面内跳转。

## 能力协商与请求

先完成既有 `zhuojian:ready` / `zhuojian:host-ready` 握手。只有后者 `capabilities` 包含 `navigation.v1` 才使用新导航；`leave-check.v1` 表示平台能执行下述离开检查；`assistant-presence.v1` 的独立协议见 [业务助手语义锚点 Bridge](assistant-presence-bridge.md)。不能凭 Skill 或 Manifest 版本推断支持情况。

```json
{
  "type": "zhuojian:navigate",
  "version": 1,
  "application_slug": "sample-review",
  "launch_nonce": "本次可信 SSO 启动 nonce",
  "request_id": "每次用户意图的唯一请求号",
  "module_key": "sample_review",
  "page_key": "sample_review.approval"
}
```

消息只允许以上字段。请求号为 8–120 个安全标识字符；模块最长 120，页面最长 160。仅发送已登记标识，不发送 URL、用户、角色、权限、Token、业务操作或内部路由。请求通过 `parent.postMessage` 发给后端配置的可信平台 origin；不得用 `*`、任意查询参数或父页面 DOM。

平台验证当前 iframe、Origin、应用、nonce、字段、目录及服务端实时权限。跨模块必须重新签发目标入口，不复用旧模块会话；导航不能自动执行 Action，也不支持跨应用或任意 URL。重复请求号绑定相同目标时不重复签票；不同目标必须用新请求号。

响应 `zhuojian:navigate-result` 带相同身份、请求号、模块和页面，`status` 为：

- `pending`：等待离开检查。
- `accepted`：请求受理，尚未完成目标加载，不能显示“跳转成功”。
- `completed`：目标 iframe 已提供可信 ready 和目标页面 context。
- `rejected` / `failed`：未完成；显示错误，保留可用原页面，不自动重试或放宽权限。

适配器 `static/zhuojian-navigation.js` 的 `navigate(moduleKey, pageKey)` 仅在收到 completed 时完成 Promise；可用 `onAccepted` 展示加载中。成功切换会卸载原文档，不应依赖旧页面 Promise 再执行业务。失败由 `onFailure` 展示；模板演示声明式 `data-zhuojian-module` / `data-zhuojian-page` 按钮。不支持时保留已有导航并明确告知限制，不能伪装成功。

## 未保存内容

平台发送 `zhuojian:prepare-leave`，字段为版本、应用、nonce 和请求号；子系统验证父窗口、Origin 和身份后，返回相同身份与请求号的 `zhuojian:leave-result`，增加布尔 `dirty`。

模板 `isDirty` 必须接入真实业务表单、上传队列及未确认草稿。异常、未知或异步检查不能被当成无修改。dirty 为真时由平台确认，取消保留原页面；新接口超时不继续跳转。旧页面未实现离开检查时，平台导航使用明确确认，不擅自假定没有草稿。离开检查不是保存接口，不在导航期间自动提交表单。

手机验收必须分别覆盖：仅浏览返回 `dirty:false` 且切换无弹窗；真实编辑返回 `dirty:true`，取消后输入仍在；保存成功后恢复干净状态；检查超时保留原页面或明确告知“子系统未响应，无法确认”，不能把超时描述成已检测到修改。不能用恒定 false、删除保护或只调整提示文案宣称误弹窗已根治。SaaS 不能跨域读取子系统表单，旧子系统缺少回应时必须列为待业务负责人适配，Skill 更新不能替代已部署代码更新。

## 独立打开与兼容

独立模式保留自身模块导航。2.5 SSO 换码可提供可选 `claims.navigationEntry`，由后端验证并随 bootstrap 返回，与可信 `platformOrigin` 组成受控入口。适配器只追加模块、页面标识；平台登录后重新校验并签发入口，子系统不拼接 `/terminal` 等内部实现路径。

2.4/2.5 旧契约保持兼容。不具备 nonce/导航入口/协商能力时保留当前可用流程并列出限制，不取消 session-check，不建立离线放行。Skill 下载本身不修改已部署页面。

## 目录与升级验收

员工导航和管理员“系统 → 模块 → 页面 → Action”使用同一 Manifest。公共查看仅表示企业内已公开业务内容，不是公共文件工作空间；个人、管理与其他分类不改变资源的现行授权与继承策略。普通筛选、弹窗及详情页签不强制注册为权限资源。

业务负责人 Codex 更新 Skill 后：盘点服务器当前源码、未同步变更和运行版本 → 最小导航/手机补丁 → 独立测试 → 部署 → 契约登记核对。禁止模板覆盖或自动扩权，不要求取得 SaaS 服务器权限。

测试至少包括跨来源 iframe、合法目标、错误 Origin/source/nonce、任意 URL 拒绝、无权/撤权、重复请求、超时、旧平台不支持、未保存表单取消、深链接、前进后退、AI 当前上下文，以及手机触摸/键盘与独立/嵌入入口。研发负责人类测试身份验证完整流程，独立受限身份验证拒绝；不得只用全权限账号宣布鉴权通过。保留手机适配规范中的真实页面、浏览器和视口矩阵，协议样例不能替代业务手机验收。
