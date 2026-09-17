# 手机适配规范发布记录

基线 81d04bd。用户后续明确授权仅发布 SaaS 与 Skill；不部署三个业务子系统。

稳定 core 1.1.7 已随 bundle-v1.4.7 发布，source `29c60332845c2e385fe7ce444dd5d557633a4542`，PR #15。全量核心测试 229 passed、41 skipped，quick_validate 通过。本机自动更新验证 1.1.6 → 1.1.7，第二次返回 SKILL_UPDATE_CURRENT 1.1.7。

- 主规范补上真实业务页面、双引擎、嵌入/独立入口、模块内页面及未测项记录要求。
- 需求参考删除“第一版不做手机适配”的冲突；只排除另造一套手机系统。用既有脚本重新生成模块需求 AGENTS.md。
- 静态扫描只判断 CSS 声明中的 width/min-width，不再把 media 断点和 max-width 当成固定宽度；表格识别 overflow:auto。
- 新增五项静态回归，相关测试 42 项通过，quick_validate 通过。

静态规则无法判断真实页面是否被父网格撑宽，不能代替实际浏览器；e2e 中 responsive_acceptance_pass 为 null 仍代表待验收，不能报手机验收通过。本候选尚未提供真机自动化能力，也未修改 Runtime 发布行为。
