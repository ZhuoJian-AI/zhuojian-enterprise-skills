# 企业 AI 底座子系统发布与开放规则

2026-11-23，Codex。规则适用于共用 SaaS 与企业独立员工入口。Builder 1.1.65 收录发布前校验、系统验收权限、按业务角色开放、受控恢复及逐入口回读。规则沿用既有 2.4 / 2.5 校验器和授权能力。

在独立目录运行 `python skills/core/zhuojian-subsystem-builder/scripts/validate_source.py --path <冻结候选>`。真实故障的候选退出码 1，报告五个新增多范围 Action。只改为已实现固定范围的修正版退出码 0。用 `git diff --check` 校验变更。SaaS 内置 Skill 与稳定分发分别核对版本和字节。

版本登记和访问授权按各实例现有机制办理。主机自动拦截、既有 Runtime 升级及员工实际可见性以各自的运行回执为准。
