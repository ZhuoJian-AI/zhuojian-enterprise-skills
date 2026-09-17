# 标准导航发布交接

基于手机适配 core 1.1.7 / `07240f8`，只更新通用规范与模板，不部署任何业务子系统，不改变 2.4/2.5 契约版本或真实授权。

新增 `references/navigation-bridge.md`、模板 `static/zhuojian-navigation.js`，提供能力协商、严格身份、同应用标识导航、离开检查与受控独立入口。模板 bootstrap 只暴露可信平台 origin 和换码提供的稳定入口；隐藏导航不代替按钮跳转。

`python -m pytest -q`：230 passed、41 skipped；包含生成模板安全/恢复套件及真实 JavaScript 适配器行为测试。源码标记检查只是接入提示，不代替跨来源、双身份、撤权、草稿及真实手机页面验收。

SaaS 已发布：source `6948688cc1be6e381c6223564ca991886d6d87d6` / manifest `1facfb38e5cc4460e8ba571e0dba82d74478567e`，维护部署 `maintenance7e2581639f3771893c2d` 于 2026-09-17 16:27:29 CST 恢复。九服务 healthy，管理员只读冒烟通过，真实授权与企业设置指纹未变。跨来源导航浏览器与 46 项隔离 PostgreSQL 测试通过；不冒充真实员工线上导航全流程或手机真机验收。

core 1.1.8 / [bundle-v1.4.8](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.8) 已发布，source `dd27315d8d397768a18310b9b531d4b86cc91fb0`（PR #17）。从干净 main 合并提交生成稳定资产；公开无登录安装返回 `SKILL_UPDATED installed 1.1.8`，重复更新 `SKILL_UPDATE_CURRENT 1.1.8`，本机正式 Skill 从 1.1.7 更新到 1.1.8 并重新读取。校验包的更新器没有使用 gh 登录凭证。

组织索引及下游通知已同步：COA #30、生产协同 #42、chairco #2、样衣 #2、生产交接 #2。通知不修改下游代码，不构成下游已验收或已发布的证据。

业务负责人后续步骤：更新 Skill → 盘点服务器源码、未同步改动和运行版本 → 最小导航与手机适配 → 双身份/桌面/手机验收 → 部署 → 契约同步。无需 SaaS 服务器登录权限；不得覆盖服务器现场改动或复制旧权限到新增模块。
