# 模块导航主题改为 Skill 发布必填

日期：2026-09-18；范围：`zhuojian-subsystem-builder`；目标版本：core 1.1.11／`bundle-v1.4.11`。

## 变更边界

- 所有经本 Skill 新发布的子系统，包括单模块及后续维护的 2.4／2.5 契约，必须在 Manifest 顶层登记四个受控颜色令牌 `presentation.moduleNavigationTheme`。颜色须与真实业务页面协调；不能仅复制 SaaS 默认紫色通过静态校验。
- Schema、源码检查、运行端点语义检查、Runtime 发布登记脚本及旧系统管理员手工登记入口都拒绝缺失或无效主题。脚手架的初始令牌与自身默认页面配色一致；页面换色须同步调整令牌。
- 桌面和手机仍需对照真实页面验证选中、未选中、键盘焦点和背景。机器能检查格式与对比度，不能单靠机器证明品牌配色一致。
- SaaS 已登记的旧版本继续使用默认色回退；Skill 更新不会停用它们，也不会自动修改 ECS 源码、运行镜像、真实授权或业务数据。本次不接触企业文化、生产协同、商品动销三套子系统。

## 验证证据

- `python -m pytest -q`：241 passed、41 skipped。
- `python C:/Users/王鑫涛/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/core/zhuojian-subsystem-builder`：Skill is valid。
- 测试覆盖脚手架默认主题、2.4／2.5 缺失主题、低对比度拒绝、无 Manifest 源码检查，以及登记前拦截。

## 下游负责人待办

逐系统核对当前服务器 Git 工作树与已运行 Manifest，保留并行改动；从页面现有设计令牌提取四个色值，补入 `subsystem.json` 和运行中的 Manifest 端点，再执行源码、端点、权限及双端视觉验收。分别部署并同步登记后，才可报告该子系统符合新版导航契约。不得直接改真实员工授权，不得将三个系统一并切换。

## 发布状态

本文件提交时，源码 PR、稳定 Release 及公开自动更新验证仍待完成；应以实际 Release 与验证记录为准，不把此文件当成已发布证明。
