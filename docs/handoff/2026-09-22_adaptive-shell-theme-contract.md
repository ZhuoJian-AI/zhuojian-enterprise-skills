# 自适应应用外壳主题契约：本地候选

## 状态

`zhuojian-subsystem-builder` core 1.1.20 的候选历史保留于下文；当前状态以文末稳定发布补充为准。

## 契约变化

- 继续只接受 `presentation.moduleNavigationTheme` 的四个完整十六进制颜色，不增加 CSS、选择器、字体、尺寸、脚本、URL 或逐模块样式。
- SaaS 可在**当前应用**范围内，将这些令牌用于模块导航、标题身份区、当前系统选中项，以及平台导航轨、通用操作和统一助手入口的边框、选中、焦点、图标与轻量晕染。
- 平台骨架、结构、名称和普通文字保持中性；其他应用入口、助手面板／回答内容与 iframe 内容不得继承当前应用主题。
- 切换应用必须同步换色，离开应用必须清除主题，禁止跨系统泄漏。
- `contractRevision` 仍为 2.4／2.5，Manifest Schema 和业务权限语义不变。

## 责任范围

- Skill 只规定以后新建／改造系统的登记与验收边界，不代替 SaaS 运行时代码。
- SaaS 前端负责读取、限制作用域、切换和清理主题。
- 已有子系统登记的四个令牌有效时无需修改业务代码或重新部署；无效主题仍由 SaaS 回退。

## 验证

- `python -m pytest -q`：423 passed、41 skipped。
- `tests/test_contract_versions.py` 新增协调式入口、平台中性和离开清理的文本契约断言。
- `git diff --check` 通过。

41 个跳过项为当前环境未启用的外部／运行时依赖检查，不计为本次通过证据。

## 稳定发布补充（2026-09-22）

- SaaS 运行时先行发布：source [PR #365](https://github.com/ZhuoJian-AI/ai-platform/pull/365) / `9f104d5bd6b6d13519a9e027204f78cfca66b1cc`，manifest [PR #366](https://github.com/ZhuoJian-AI/ai-platform/pull/366) / `3cbe964a67ac2882d7197093ca8e681d15f6e438`。维护部署 `maintenanced44c4361ededc79e9062` 于 21:39:17 CST 恢复 normal，九服务 healthy、schema 仍为 `0080_assistant_fence`，未改后端、权限、存储或业务数据。
- Skill [PR #37](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/pull/37) 合并为 `f429ee1372cbf211d2228bd2641378586b57ff3a`；从该干净主线构建并于 21:54:36 CST 发布 [bundle-v1.4.20](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.20)。core 为 1.1.20，其余四个 Skill 版本和内容摘要不变。
- 九个公开资产摘要全部与本地构建匹配；核心 ZIP SHA-256 为 `be23f708281eea57c3510ed070420cc4151940384ed1ffb1c3922f99fa4be79f`。CI `core-tests` 成功，本地全量为 423 passed、41 skipped，quick validation 通过。
- 公开 latest 全新安装 1.1.20、重复 CURRENT、从公开 bundle-v1.4.19 安装 1.1.19 后升级到 1.1.20 均通过；本机稳定安装亦从 1.1.19 更新到 1.1.20，并重新通过 quick validation。
- 默认 urllib 通道在发布前检查时连续三次出现网络失败，未继续无限重试，也不写成默认网络路径通过。上述公开安装使用一次性 curl HTTPS 传输桥，经既有 `127.0.0.1:7897` 代理获取真实 GitHub Release；原更新器继续负责 URL 白名单、版本、SHA-256、压缩路径／链接安全、原子替换和回滚。
- 真实张三桌面和李四手机模拟端均核对企业文化暖绿与生产协同冷蓝的 SaaS 外壳切换；公网八视口自动回归通过。李四首次切换企业文化时出现一次可恢复 Bridge 就绪延迟，页面重试后恢复；该现象不扩大为真机或网络零延迟保证。
- 本发布仅更新开发接入契约，不部署 Runtime helper 或业务 ECS。企业文化、生产协同、商品动销和公司共享盘既有主题登记有效，均未修改或重新部署；后续新建／实质改造继续按本契约验收。
