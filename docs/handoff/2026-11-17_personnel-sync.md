# 现有 Runtime 接入原系统人员同步

主责：SaaS 提供公共接口、授权和原员工生命周期；企业采集程序适配来源；本 Skill 提供按需接入知识和可选投递工具。保留 SaaS 手工管理、现有正常同步、员工角色与历史归属。不自动迁移企业、不重发业务子系统。

core1.1.63 候选补充 `references/personnel-sync.md`、知识导航、Python标准库投递工具与可选systemd模板；Runtime投影识别平台实际声明的 `personnelSync`。普通企业插件沿原动态管理员通道发现五项来源管理操作，不复制一套插件登录或权限。SaaS配套源码 PR1231；Skill安装不等于其已部署。

工具与 SaaS `deploy/enterprise-directory/directory_sync.py` 同源，覆盖来源身份绑定、原ID版本、持久化待发批次、丢失回执后原请求重传和来源缺失不推断离职。企业专用数据库结构、凭据、主机和业务数据不进核心 Skill。

2026-11-17 Windows定向测试：`python -m pytest --noconftest tests/test_personnel_sync_sender.py tests/runtime_host/test_platform_capabilities.py -q`，215 passed。完整测试、公司精确源码测试及正式分发待结果；候选修改不冒称稳定版、双账号更新或服务器自动同步完成。
