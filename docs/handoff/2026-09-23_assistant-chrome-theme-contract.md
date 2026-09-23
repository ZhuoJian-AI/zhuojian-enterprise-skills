# 当前应用主题与统一助手外壳：Skill 本地候选交接

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

当前是独立 worktree 的本地候选：未推送、未开 PR、未合并、未发布 `bundle-v1.4.21`，本机已安装的稳定 core 1.1.20 不会被本次源码编辑替换。SaaS 前端候选另在 `ai-platform` 仓库；先完成 SaaS 受控发布与真实桌面／手机核对，再按 Skill 仓库规则合并、构建并公开发布新稳定包。企业文化、生产协同、商品动销和公司共享盘现有主题登记无需因本次规范变化重新部署；若未来发现个别登记无效，应在该子系统发布任务中单独处理，不能把本次 Skill 更新称为已修复。
