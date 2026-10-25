# 共享 OSS 档案校验入口补丁

core1.1.46 已完成公开分发后，沿真实初始化链继续检查，发现 `scripts/validate_storage_profile.py` 仍硬编码 `rootPrefix=apps`。Runtime 与 gateway 已支持 enterprise-v1，但开发前必经的独立校验入口会拒绝正确共享桶档案。原46 CLI 对有效企业隔离档案返回1，补丁47对完全相同输入返回0；本机红绿回执在 `audit-2026-10-25/multi-owner-self-service-fix/validator47/red-green.actual.json`。

本补丁只令校验器按 Runtime organizationId 的规范 UUID、environment 三个有效值派生 enterprise-v1 的精确前缀，拒绝错企业、错环境、路径越界、未知模式与不完整身份；无 namespaceMode 的旧 apps 档案及显式 legacy-apps 保持兼容。实际 CLI 17 项允许/拒绝与版本契约4项共21 passed；没有放宽存储凭据、企业权限或员工权限。

core **1.1.47 / bundle-v1.4.50 已公开并完成双账号限定同步**，保留2.4/2.5，不覆写已公开bundle49。本补丁没有部署Runtime、修改云IAM/桶或迁移文件，SaaS上线仍单独处理。

## 正式发布与同步结果

- [PR #95](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/pull/95) 合并 source `e0d048b8b8ac51bead72fde485e7db4c9b9003a8`；[PR CI 40183938259](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/actions/runs/40183938259) 与 [main CI 40184146854](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/actions/runs/40184146854) 均 **840 passed / 77 skipped / 1 warning**；Windows与Linux定向各 **21 passed**。
- [bundle-v1.4.50](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.50)，Release ID `423318318`，于 **2026-10-25 18:21:19 CST**（`2026-10-25T10:21:19Z`）公开。十匿名资产、四latest入口、八selector及tag/source身份通过；其他五个Skill ZIP与独立updater保持bundle49原字节。
- 原updater隔离core新装、**1.1.46 → 1.1.47** 升级和CURRENT通过，两隔离目录各182个包文件逐字匹配；legacy新装/CURRENT1.2.0通过。个人账号结果另行计量：`codex02`与`王鑫涛`各完成本补丁 **5路径**备份、CAS和公开ZIP精确字节核对，其中1个新增；两边范围外原样保留。各自原updater通过正常urllib读取固定bundle50 manifest，均返回 `SKILL_UPDATE_CURRENT 1.1.47`。不声明个人目录全部182文件字节一致。
- 本机证据：`audit-2026-10-25/r50pub/public.actual.json`、`r50final/frozen-assets.json`、`multi-owner-self-service-fix/sync50/apply-e0d048b8/result.json`及其备份/journal。收尾仅更新仓库文档，不修改Skill包或重发资产。
