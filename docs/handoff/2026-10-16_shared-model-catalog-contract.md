# 共享模型目录与子系统委托契约

责任：Builder Skill规定子系统接入边界；SaaS负责业务控制与对应调用工具，独立网关负责供应商、上游凭据和共享模型目录。独立AI项目持各自项目Key；SaaS子系统仍委托SaaS，不持模型Key、不另建供应商或模型目录、不直连fallback。共享模型不共享企业/员工权限、业务数据、任务或审计；按能力选择并保留项目默认型号，registered不等于实测。

仅核心Skill入口、platform-contract参考、1.1.33版本/changelog及对应版本测试；不改Manifest 2.4/2.5、Schema、Runtime、模板、更新器或其他四个Skill。目录出现视频模型不代表SaaS已实现视频业务工具。旧学院按用户最新要求排除，不因Skill更新迁移旧项目。

验证：核心 `python -m pytest -q` 为521 passed、54 skipped、124 subtests、1个既有Starlette警告；quick_validate通过，diff检查通过。Windows依赖使用工作区已有包；未修改系统Python或全局代理。未做新稳定Release、未同步两账号、未修改或部署任何业务服务；源码PR合并与稳定发布后，再备份精确同步两账号并记录来源版本。
