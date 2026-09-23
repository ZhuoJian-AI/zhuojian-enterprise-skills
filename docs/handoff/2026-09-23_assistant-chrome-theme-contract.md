# 当前应用主题与统一助手外壳：Skill 发布交接

## 责任与契约

- SaaS 前端实现运行时主题作用域；Skill 只约束子系统开发与验收，不能替代 SaaS 的代码发布。业务子系统仍负责自己的页面与四字段 `presentation.moduleNavigationTheme` 登记。
- 现有 core 1.1.20 只允许主题协调统一助手入口，明确禁止助手面板跟色。为了与本次 SaaS 候选一致，core 1.1.21 候选把范围收窄地扩展到**同一助手**的外框、顶部、选中模式、输入焦点与可用操作控件；回答正文、确认／拒绝、警告／错误、其他应用入口与业务 iframe 不跟色。切换应用换色，离开应用或遇到旧登记缺失／无效主题时回退平台默认色。
- 仍只接受四个受控颜色，不接收 CSS、选择器或逐模块样式。不新增 Manifest 字段、不改变 `contractRevision=2.4/2.5`、员工权限、Action 或审批协议。当前主题登记有效的既有子系统无代码和企业 ECS 部署需求。

## 源码与验证

- 更新 `SKILL.md`、`references/module-navigation-migration.md` 和 `references/platform-contract.md` 的主题边界与桌面／手机验收点；增加 `CHANGELOG.md` 候选记录，`skill-version.json` 调至 1.1.21，调整契约回归断言。
- 在 `skills/core/zhuojian-subsystem-builder` 运行 `python -m pytest -q`：423 passed、41 skipped。
- 运行 `python C:/Users/王鑫涛/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/core/zhuojian-subsystem-builder`：`Skill is valid!`。
- `git diff --check` 通过。未跑公开安装／升级验收；这些必须以合并后不可变 Release 包执行。

## 发布状态和下游

## 稳定发布补充（2026-09-23，以本节状态为准）

- SaaS 前端先行发布：源码 [PR #377](https://github.com/ZhuoJian-AI/ai-platform/pull/377) / `e94ff16`、清单 [PR #378](https://github.com/ZhuoJian-AI/ai-platform/pull/378) / `d3689a9`，受控部署 `maintenance783341d08946c2badeec` 于 13:10:06 北京时间恢复 `normal`，九服务健康。真实 `zhangsan` 桌面 1440px／手机模拟 390px 只读核对首页四卡和企业文化助手主题作用域通过；未测真机与危险写入。
- Skill [PR #39](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/pull/39) 经 `core-tests` 通过后合并为 `37cffdb0087d3a300ad3627526bb2d00bf4b08d4`。从该干净主线构建并公开发布 [bundle-v1.4.21](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.21)，core 为 1.1.21；其余四个 Skill ZIP 与 1.4.20 的摘要完全相同。九个公开资产各自下载并核对 SHA-256 一致，核心 ZIP 摘要为 `7d0d2c01d242fe8d064994a6f595b75d96f54dee90ca8fa1d12f7ef27e88ae06`。
- 合并主线重新运行 core 全量测试：423 passed、41 skipped；Skill quick validation 通过。公开无登录全新安装 1.1.21、重复检查 `SKILL_UPDATE_CURRENT`、本机托管副本 1.1.20→1.1.21 更新和更新后校验通过。默认 Python urllib 传输在本机代理下连续三次 `Remote end closed connection without response`，上述安装仅将下载传输临时改用既有代理下的 curl；原更新器继续执行 URL 白名单、版本、摘要、归档路径与原子替换校验，不能把默认联网通道记为已修复。本机交接 Skill 自动同步尝试因同一代理读超时给出 `MANAGED_SKILLS_WARNING`，未改变既有交接包。
- 本次没有新增 Manifest 字段、升级 2.4／2.5、更新业务 Runtime helper、修改员工授权或部署任何企业 ECS。企业文化、生产协同、商品动销和公司共享盘的现有登记无需为该外观规范重新发布；业务数据／流程和款号匹配问题均不在本次修复范围。
