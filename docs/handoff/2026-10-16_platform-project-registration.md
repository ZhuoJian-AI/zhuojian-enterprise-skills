# 平台项目归属与入口验收规范

本次主责为Skill：用户要求新系统上线后在平台管理员端正确显示、真实域名可点、有后台接好管理入口并保留原站兼容，且明确区分企业子系统和独立项目。企业子系统仍归所属企业，通过Runtime/Manifest登记并保留SaaS统一身份/权限；独立项目走服务器部署Skill的运营清单与管理接入。独立ECS或域名不改变企业归属。

核心Skill入口与首次部署收尾增加按需参考，要求实际平台管理员页面可见、域名和管理入口实点、桌面/手机结果及未测项；healthy、Wiki或发布器登记不代替平台目录验收。原站原密码并行适用于独立项目及已有授权兼容入口，不增加企业子系统的身份绕过。普通URL不能冒充免登录控制面板；平台能力/权限不足时按当前任务授权跨层完成，未验项如实交接，不转嫁业务方索Token或虚构完成。

修改范围为核心SKILL、一个新增reference、direct-ecs-deployment收尾、skill-version1.1.34、CHANGELOG及既有版本断言。contractRevision2.4/2.5、Schema、Runtime、模板、更新器及其他四个Skill不变。两账号本机范围另含已获授权的服务器部署Skill，分别由其源仓库交付。本轮不修改或部署SaaS、业务子系统、独立项目或旧学院。

验证：固定Python3.12复用既有工作区依赖，完整核心521 passed、54 skipped、124 subtests、1个既有Starlette警告，耗时22.98秒；quick_validate通过；修改文档44本地文件链接无缺失；git diff --check通过。独立审查试跑企业管理页、独立原密码站点、企业独立ECS但缺Root权限、只有URL无SSO四种场景，无P1；按已承诺授权范围验收实际管理能力，不强制无关任务升级SSO。

以上为候选阶段验证；以下正式发布证据取代候选状态。双账号基线/备份在本机audit-2026-10-16/skill-project-directory-contract，原有无关文件、缓存和本机差异不得批量覆盖。

## 正式发布与安装

- [PR70](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/pull/70)合并为`b4bb1b61afad386d09ac02871db18074ffe98fb9`；PR CI38925640905与main CI38926077954均成功，Windows CI为522 passed、53 skipped、1 warning。仅文档/版本断言变化，无运行时改动。
- 从干净合并源码按既有发布换行格式构建，于2026-10-16 23:45:28北京时间发布[core1.1.34 / bundle-v1.4.35](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.35)。九资产无认证下载SHA与本机构建一致；其他四个Skill ZIP与bundle-v1.4.34完全一致。核心ZIP SHA256为`3222406677318a5aabf9eeb8e956b9fa627bb10c85033585910a8f1bd414970d`。
- 公开原始更新器在隔离目录的新装1.1.34/CURRENT、1.1.33升级1.1.34/CURRENT均成功；两个隔离安装各159个公开包文件逐字匹配，无传输替换。证据为`public-release-verification.json`和`public-updater-verification.json`。
- 23:47:48按用户授权完成codex02与王鑫涛两个账号各6项Builder、5项服务器部署Skill的精确同步。先备份108份原件，按原基线CAS核对，22目标写入后两账号同相对路径SHA全部一致，非范围文件与集合保持；未整目录覆盖。`exact-sync-receipt.json` SHA256为`e462064302325cdea8ff5173f88d89f2c781d7d28fee9976c313715602b6e6e7`。
- 两个实际账号的原更新器针对固定公开1.1.34清单均返回`SKILL_UPDATE_CURRENT 1.1.34`。公开ZIP全文件只读比对各158/159一致；唯一差异是既有本机历史交接`docs/handoff/2026-10-12_saas-browser-surfaces-local.md`，按授权边界保留，未为整包一致覆盖。公开`.env.example`模板哈希一致。不能把隔离新装159/159混同于实际账号安装。
- 服务器部署Skill对应[PR73](https://github.com/ZhuoJian-AI/zhuojian-server-deploy/pull/73)，main`9476f9aa0f0b19336ca78cce04af65e64fb30b85`，PR/main全部五项CI成功；其本机SKILL仅插入两处规则并保留安装元数据，另同步四项指定参考/规则文件。此前公开ECR429重试记录保留，不算测试通过证据；最终真实通过另有回执。

本轮主责为Skill；SaaS、Runtime、独立项目和旧学院没有修改、部署或新增业务操作。现有系统是否满足新增规则仍由各自已授权任务的实际验收证明，不能从Skill发布推断运行时完成。
