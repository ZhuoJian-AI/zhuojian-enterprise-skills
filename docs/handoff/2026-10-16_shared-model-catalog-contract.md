# 共享模型目录与子系统委托契约

责任：Builder Skill规定子系统接入边界；SaaS负责业务控制与对应调用工具，独立网关负责供应商、上游凭据和共享模型目录。独立AI项目持各自项目Key；SaaS子系统仍委托SaaS，不持模型Key、不另建供应商或模型目录、不直连fallback。共享模型不共享企业/员工权限、业务数据、任务或审计；按能力选择并保留项目默认型号，registered不等于实测。

仅核心Skill入口、platform-contract参考、1.1.33版本/changelog及对应版本测试；不改Manifest 2.4/2.5、Schema、Runtime、模板、更新器或其他四个Skill。目录出现视频模型不代表SaaS已实现视频业务工具。旧学院按用户最新要求排除，不因Skill更新迁移旧项目。

验证：核心 `python -m pytest -q` 为521 passed、54 skipped、124 subtests、1个既有Starlette警告；quick_validate通过，diff检查通过。Windows依赖使用工作区已有包；未修改系统Python或全局代理。未做新稳定Release、未同步两账号、未修改或部署任何业务服务；源码PR合并与稳定发布后，再备份精确同步两账号并记录来源版本。

## 正式发布补充

上述为候选阶段。PR #68已合并为main `662258865d36d9ab998ed7b0dc54d50e21a9c8db`，main [Core Skill CI 38851040609](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/actions/runs/38851040609)成功；从该干净合并提交构建并发布[core 1.1.33 / bundle-v1.4.34](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.34)。其他四个Skill ZIP的SHA-256与bundle-v1.4.33完全相同。

九个资产均通过无认证公开GET和SHA-256核对；一次Schannel握手失败经当前同一代理有界重试恢复，不计作第一次成功，不改TLS/订阅/系统代理。原始更新器通过公开最新稳定通道新装1.1.33、CURRENT及隔离1.1.32→1.1.33升级；没有以file URL或改transport代替公开分发验收。

两个账号均先备份至各自`.codex/skill-backups/20261016-builder-1.1.33/`，再仅同步本次`SKILL.md`、`references/platform-contract.md`、`skill-version.json`、`CHANGELOG.md`、`tests/test_contract_versions.py`五文件。这五文件逐字节匹配公开ZIP；其他文件各162/153个保持，两个安装原有`docs/handoff/2026-10-12_saas-browser-surfaces-local.md`与公开包的本地差异保留，codex02的九个既存pycache也未清理，因此不宣称完整158文件全部一致。两边原始更新器均返回`SKILL_UPDATE_CURRENT 1.1.33`，quick_validate通过。本轮无其他Skill安装、无业务运行时部署，旧学院保持原状。
