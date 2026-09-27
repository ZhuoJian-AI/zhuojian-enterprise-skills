# 连续自适应纠错规范

任务 `CONTINUOUS-RESPONSIVE-CONTRACT-20260927`，Codex；基线 `a9a545b`，部署规则 `43dff14`。用户要求记录此次宽屏失误，避免反复针对单一电脑/手机尺寸修补。

## 原因与调整

SaaS 员工首页背景误套正文限宽，既有固定视口验收未覆盖宽屏和浏览器缩放后的实际可用空间。本仓负责后续开发规范，当前运行时代码由 `ai-platform` 修复；规范本身不能修复已上线页面。

补充核心 Skill 入口、`references/platform-contract.md` 及生成项目 `AGENTS.md`：电脑/手机分别设计交互，各自内部连续自适应；背景铺满与正文限宽分离，内容可收缩/换行，卡片容纳可见内容。在固定矩阵之外持续缩放同一会话，覆盖窄窗口、超宽屏、断点两侧、侧栏变化、长内容、低高度及失败状态；检查内部裁切、操作可达与业务状态保持，区分模拟与真机。

没有新增协议字段、改变 2.4/2.5、修改业务模板运行代码或升级版本号。规则适用于后续相关页面开发；不会自动重做或部署已接入的生产协同、商品动销、企业文化或公司共享盘。下游无立即迁移截止日期。

## 验证与状态

- `python C:/Users/王鑫涛/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/core/zhuojian-subsystem-builder`：通过。
- `python -m pytest skills/core/zhuojian-subsystem-builder/tests/test_generated_native_template.py skills/core/zhuojian-subsystem-builder/tests/test_native_template_responsive.py -q`：4 passed，12.93s。
- 本次为文档修正，未新增匹配文案的测试；既有生成与浏览器模板检查不代表所有业务页面已自适应。
- 当前是本地源规范候选，未推送、未合并、未发布稳定 Skill 包。本机已安装稳定包仍为 1.1.23；当前助手另通过全局 `AGENTS.md` 的长期要求执行此规范。
- 发布范围：后续经授权合并并发布 `zhuojian-enterprise-skills` 稳定包；无需部署 SaaS 服务或企业 ECS。本次 SaaS 修复、服务构建及浏览器验证在对应 `ai-platform` 交接单列。
