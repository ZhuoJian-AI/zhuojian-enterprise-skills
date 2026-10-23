# SaaS 企业生命周期与模型网关契约

核心 Skill1.1.41 仅补 `references/platform-contract.md` 的平台职责：SaaS 以稳定企业 UUID 管理开户、收编、改名、停用、重试和明确测试豁免，连接从加密数据库统一读取，模型中心动态列出全部企业。独立网关项目列表不能替代企业清单。

SaaS 负责员工身份、登录和当前业务授权；网关只校验受限机器／项目身份和企业隔离。Runtime、子系统与 Skill 不再创建另一套网关企业或绑定 JSON，业务负责人无需提供模型 Key；已有 SSO／Action 验签、企业与权限检查继续执行。

本次除这一个参考外，只增加所需 patch版本与 CHANGELOG、任务及交接。接入2.4／2.5、Schema、模板、更新器、其他企业交接 Skills 和运行时代码保持。两账号对应参考已先备份并精确同步；稳定发布后仅补必要版本元数据，保留各账号无关文件与本地差异。

发布顺序：已有核心测试与 quick validation，正常 reviewed PR、精确 main CI，干净合并提交构建新的不可变 bundle，公开资产 SHA 与原更新器隔离新装／CURRENT 核对。只合并 main 不会更新用户的稳定通道；本次发布不重发 SaaS、Runtime 或业务系统。

本地核心完整套件607 passed／56 skipped／1个既有Starlette弃用警告，24.02秒；quick validation、两个相关工作流YAML及diff检查通过。patch版本所需的既有版本断言同步为1.1.41；不添加镜像实现的测试或改动运行逻辑。跳过仍是既有Windows/POSIX语义和须在生成项目执行的原始模板用例，不等同运行时或真机验收。
