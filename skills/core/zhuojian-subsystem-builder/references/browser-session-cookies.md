# 手机内嵌浏览器的 SSO 会话 Cookie

修改登录、修复手机钉钉/WebView 中“平台能登录、业务页却未登录”，或维护会话模板时读取。这里说明通用接入问题；具体企业、客户端、运行版本和验收记录放在企业交接或项目 handoff，不写入公共 Skill。

## 先区分授权失败与会话未回传

平台导航可见或 launch 成功，只能证明入口已签发，不能证明业务页已建立会话。按同一轮请求核对：SaaS launch → 子系统后端换码 → SSO 响应 Cookie 与 302 → 业务页请求 Cookie → 页面/业务 bootstrap 的真实结果。

若换码成功且服务器已建立有效会话，但重定向后的请求完全没有 Cookie，业务页会返回 401，并可能原样显示“Open this module from ZhuoJian SaaS”；SaaS 外壳随后因缺少可信 ready 显示“业务页面尚未建立连接”。这类现象不等于角色未生效、服务正在升级或员工从错误入口进入。重复扩权、重置密码、删 Cookie 校验或直接放行业务页都不能修复会话传输。

部分手机内嵌浏览器可能丢弃或不回传 `SameSite=None; Partitioned` Cookie。不能仅凭 UA 判断是哪一个属性触发，也不能推断所有 Android/钉钉版本都失败。分别核对是否真正签发、请求是否携带、签名/随机令牌是否匹配、会话是否存在及过期、后续业务是否获权。日志只保留必要元数据，不记录 Cookie 值、短码、签名链接或凭据正文。

## 当前模板的兼容方式

- 保留原 `zjsid` 的 `HttpOnly; Secure; SameSite=None; Partitioned` Cookie，继续支持具备相应能力的跨站点嵌入。
- 同时签发独立名字的 `zjsid_same_site`，属性为 host-only、`Path=/; HttpOnly; Secure; SameSite=Lax`，不设置 Domain 或 Partitioned。两者必须引用同一个签名不透明标识、同一服务端会话和相同有效期，不复制完整 claims 到浏览器。
- Lax Cookie 用于同站点嵌入，例如同为 HTTPS 且位于同一可注册域名下的 SaaS 与业务子域；跨源不必然跨站点。它不能单独解决真正跨站点且拒绝第三方 Cookie 的浏览器。遇到后者应核对平台与客户端实际支持，不扩大 Domain、在 URL 携带长期令牌或绕过统一登录。
- 读取合法的多个 Cookie 请求头，逐候选验证签名和有效服务端会话；过期兼容 Cookie 不遮蔽有效原 Cookie，伪造值不得恢复身份。自定义服务沿用自己的安全随机令牌/签名和存储格式，仅增补兼容传输，不换掉 SaaS 权限链。
- SSO 显式轮换时撤销浏览器携带的旧候选，并同时设置两 Cookie。普通、迟到或失效请求不得设置旧 Cookie、发送可能抹掉新登录的过期 Cookie，或通过 upsert 复活已撤销会话。清除以服务端撤销为准，两 Cookie 都不能再次获得访问；保留模板已有的并发保护。

SaaS 负责身份、实时授权和公共 SSO/Bridge；子系统负责自己的 Cookie、服务端会话和业务入口校验；Skill 负责模板与验收契约。多个子系统使用同类模板时属于共性兼容风险，不是整台服务器或所有用户必然故障。修改 Skill 不会自动修复已部署的系统，须按获授权的实际企业应用清单逐个检查、测试、发布和登记，保留各自最新功能、角色、数据与存储。

## 验收与范围

模板测试应覆盖只保留 Lax Cookie 跟随 302、原 Cookie 兼容、伪造/过期/撤销/缺失拒绝、失效候选回退、两 Cookie 同会话、重复请求头，以及旧模块迟到响应不覆盖新会话。业务系统还须验证真实 SSO、bootstrap、页面/Action 授权和无权拒绝。

电脑浏览器、手机尺寸模拟、实际手机钉钉/WebView 分别记录。UA 模拟不等于对应内核或真机；健康检查、登记 healthy、合成 Cookie 测试不能替代员工手机实际进入。报告代码修改、提交、发布、各客户端结果与未测项，不把兼容代码上线直接称为全部真机恢复。

依据：[MDN Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie)、[同站点 Cookie 示例](https://github.com/GoogleChromeLabs/samesite-examples)。保持既有 2.4/2.5 协议与权限，不新增 Manifest 字段。
