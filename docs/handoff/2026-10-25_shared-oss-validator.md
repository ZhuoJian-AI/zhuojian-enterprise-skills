# 共享 OSS 档案校验入口补丁

core1.1.46 已完成公开分发后，沿真实初始化链继续检查，发现 `scripts/validate_storage_profile.py` 仍硬编码 `rootPrefix=apps`。Runtime 与 gateway 已支持 enterprise-v1，但开发前必经的独立校验入口会拒绝正确共享桶档案。原46 CLI 对有效企业隔离档案返回1，补丁47对完全相同输入返回0；本机红绿回执在 `audit-2026-10-25/multi-owner-self-service-fix/validator47/red-green.actual.json`。

本补丁只令校验器按 Runtime organizationId 的规范 UUID、environment 三个有效值派生 enterprise-v1 的精确前缀，拒绝错企业、错环境、路径越界、未知模式与不完整身份；无 namespaceMode 的旧 apps 档案及显式 legacy-apps 保持兼容。实际 CLI 17 项允许/拒绝与版本契约4项共21 passed；没有放宽存储凭据、企业权限或员工权限。

core候选1.1.47，保留2.4/2.5；计划独立新bundle-v1.4.50，不覆写bundle49。其他五个Skill保持原包。正式PR/main CI、公开下载与两账号仅本补丁路径的备份/CAS同步由根任务继续记账。本补丁尚未部署Runtime或迁移云文件，SaaS上线仍单独处理。
