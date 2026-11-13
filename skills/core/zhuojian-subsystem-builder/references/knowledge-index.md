# 知识索引

这是给 AI 的检索入口，不是执行清单。按当前问题选资料，可用文件名或关键词搜索具体章节；已有证据足够时不重复加载。无需为了一个样式修复遍历整个知识库。

“没同步”可能是代码未发布、Manifest 被拒、入口指向旧版本、会话或业务授权问题，需由现场证据判断；“读不到配置”也不等于未初始化。

## 现有系统、发布与排障

- [代码已改但线上没变、同步失败、现有部署定位](existing-system.md)
- [服务器长期访问记忆](server-access-memory.md)
- [ECS 首次接入](ecs-first-access.md)
- [SSH、VPN 与代理访问](ssh-access.md)
- [ECS 直接发布](direct-ecs-deployment.md)
- [原生聚合与扩展](native-aggregation.md)
- [平台项目归属与入口验收](platform-project-registration.md)
- [子系统可用性与维护提示](subsystem-availability.md)

## 身份、权限与登录

- [SaaS 授权有效、三方员工同步、旧账号与 C 端边界](employee-authority.md)
- [统一身份的入口核查与验收](identity-acceptance.md)
- [员工目录与历史身份核查](employee-identity.md)
- [内嵌浏览器会话 Cookie](browser-session-cookies.md)
- [操作权限与记录归属](action-permission-scopes.md)
- [工作空间与业务授权边界](workspace-access.md)
- [企业插件与外部宿主接入](external-agent-access.md)

## 业务、助手与页面

- [业务提效设计与交付](business-ai-delivery.md)
- [资料识别与对象归属核对](business-identity-review.md)
- [三入口与来源边界](platform-contract.md)
- [界面、身份、助手、双端交付的详细结果要求](implementation-notes.md)
- [模块导航与安全迁移](module-navigation-migration.md)
- [标准导航 Bridge](navigation-bridge.md)
- [业务目标入口 Bridge](assistant-entry-bridge.md)
- [当前页面的业务提示](assistant-page-suggestions.md)
- [业务流程知识、当前页与跨页检查](assistant-workflow-guidance.md)
- [业务助手语义锚点 Bridge](assistant-presence-bridge.md)
- [通用消息委托与通知业务边界](message-delivery.md)

## 企业协作、文件与恢复

- [企业服务器内业务服务对接](intra-enterprise-service-integration.md)
- [同企业多人开发、Git 与备份](shared-enterprise-development.md)
- [跨系统对接与受控配置](cross-system-integration.md)
- [多系统对接与整条业务流程验收](multi-system-integration.md)
- [文件存储与 OSS 迁移](object-storage.md)
- [外部资料源只读访问](external-readonly-files.md)
- [备份覆盖与恢复验收](recovery-acceptance.md)
- [跨主机与跨地域迁移](region-migration.md)
- [ECS 数据盘与容量迁移](data-disk-capacity.md)

## 初始化、研发方式与更新

- [管理员与服务器初始化](admin-bootstrap.md)
- [独立 Skill 与研发通道](plugin-development.md)
- [可选的插件研发执行端接入](plugin-runtime-bootstrap.md)
- [Runtime 存储初始化与自动接入](runtime-storage-bootstrap.md)
- [企业交接 Skill 自动同步](managed-handoff-skills.md)
- [Skill 稳定版更新](skill-updates.md)
- [企业交接、项目现状、知识来源与接续](project-knowledge.md)

## 工具入口

参数以实际 `--help` 为准。这些工具可单独组合使用，不组成固定业务流水线。

- `scripts/inspect_subsystem.py --path <目录> --json`：源码线索；只读扫描不能证明进程、数据或线上版本，也不能把根目录没 Manifest 当成空系统。
- `scripts/validate_source.py --path <实际含 subsystem.json 的目录>`：源码及 Manifest 契约；嵌套项目选择实际接入目录。
- `scripts/validate_endpoint.py`：已运行端点；`scripts/publish_subsystem.py`：登记与同步结果。
- `scripts/e2e_acceptance.py`：登记前技术预检；真实员工 SSO 和本人业务操作另有证据。
- `zhuojian-runtime doctor / preflight / ensure-app / deploy`：标准 Runtime；已有专用发布器见企业交接，不为套命令擅自重新初始化。
- `scripts/scaffold_subsystem.py --help`：确需新项目时再用模板；需求澄清可读[模块需求](../模块需求/SKILL.md)。
