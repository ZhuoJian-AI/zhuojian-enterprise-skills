# 手机适配规范本地候选

基线 81d04bd，稳定 core 仍是 1.1.6。本轮不发布 Release、不覆盖已安装 Skill。

- 主规范补上真实业务页面、双引擎、嵌入/独立入口、模块内页面及未测项记录要求。
- 需求参考删除“第一版不做手机适配”的冲突；只排除另造一套手机系统。用既有脚本重新生成模块需求 AGENTS.md。
- 静态扫描只判断 CSS 声明中的 width/min-width，不再把 media 断点和 max-width 当成固定宽度；表格识别 overflow:auto。
- 新增五项静态回归，相关测试 42 项通过，quick_validate 通过。

静态规则无法判断真实页面是否被父网格撑宽，不能代替实际浏览器；e2e 中 responsive_acceptance_pass 为 null 仍代表待验收，不能报手机验收通过。本候选尚未提供真机自动化能力，也未修改 Runtime 发布行为。
