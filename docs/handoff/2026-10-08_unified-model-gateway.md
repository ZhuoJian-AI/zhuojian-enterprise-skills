# 统一模型网关与业务 AI 控制面

2026-10-08，依据用户已确认的统一网关方案，开发基于最新 `origin/main` 的 `539d060c0bd787deb6239597a68e81ddc7e2e24a`，分支 `codex/builder-unified-model-gateway-20261008`。

## 方案与范围

- 独立模型网关维护已接入能力的上游供应商账户、密钥与路由主配置；SaaS 仍是员工业务 AI 的唯一控制面，负责模型能力授权、权限、上下文、工具编排、确认及业务审计。
- 子系统继续只走 SaaS 受控能力，不获取供应商/网关 Key，也不直连模型网关。保留 SaaS 管理入口时，供应商配置读写调用网关管理层，不复制一套上游秘密和路由真相源。
- 未经网关公开支持的向量、语音等能力沿用现有专业通路；实际适配、权限及目标环境验收完成后才能声称迁到网关。专业通路的保留不是子系统直连供应商的例外。
- 修改 Builder 的 `SKILL.md`、`references/platform-contract.md`、`references/business-ai-delivery.md`；同包页面建议、流程指导及“模块需求”中的旧供应商归属句同步修正，后者聚合 `AGENTS.md` 由原 `build_agents.py` 重新生成。准备 core 1.1.31 的版本、更新记录和既有版本测试断言，对应下一稳定 bundle-v1.4.32。没有修改独立企业交接 Skill、Schema、模板、身份、Action/Bridge/Runtime 协议、SaaS、子系统或前端。

## 检查与状态

已读取安装版 core 1.1.30、当前源码规则和稳定发布要求。原始 `update_skill.py` 在安装版的隔离副本检查，输出 `SKILL_UPDATE_CURRENT 1.1.30`；原始 `update_managed_skills.py installed` 指向同一不含交接 Skill 的隔离目录，输出 `MANAGED_SKILLS_CURRENT 没有匹配的交接 Skill`。两命令退出0；这不代表真实安装目录中的企业交接 Skills 已更新。本轮不修改两个账号的安装版，也不覆盖本机未知改动。

最终使用现有 CPython 3.10.21 发布测试环境，未安装或改动依赖：

```text
cd skills/core/zhuojian-subsystem-builder
<existing-py310>/python -m pytest -q --basetemp <task-audit>/pytest-temp-final -o cache_dir=<task-audit>/pytest-cache-final
```

- 完整核心套件 **522 passed / 53 skipped / 1 warning，21.75秒，退出0**；53跳过为Windows不能验证的3项POSIX语义及50项仅在生成项目执行的原始模板检查，既有生成项目子套件仍执行。警告为现有 AnyIO 别名弃用。原始日志在本机 `audit-2026-10-08/builder-gateway-update-check-20261008/core-full-final.log`。
- 首轮 CPython 3.12 环境为520 passed/54 skipped/1 failed；唯一失败是既有版本测试固定1.1.30，与新元数据1.1.31不符，现已同步该断言，默认2.5和支持2.4/2.5断言不变。额外跳过是该环境没有Playwright，最终改用依赖齐全的既有发布环境完成全套；不把首轮报作通过。
- 系统 `skill-creator/scripts/quick_validate.py` 对 Builder 本体退出0；新增6处相对链接及目标锚点、`git diff --check` 通过。
- 随包“模块需求”单独快速校验退出1：历史 `name: 模块需求` 不符合新版校验器ASCII hyphen-case要求；未改安装版与候选均同样失败。此次不重命名其稳定入口，不将该项报作通过。聚合AGENTS用原生成器生成，仅两处供应商归属句发生内容变化。
- 没有修改Python执行逻辑、模板、Schema、兼容入口或企业交接Skills；没有新增镜像、运行时发布或具体业务/真机验收。现有子系统无需因本次规则更新自动同步或重建。

## 协调线后续发行

本分支仅本地提交，尚未推送、合并、稳定发布或双账号同步。`bundle-v1.4.32` 在本轮远端标签检查时未占用，发行前应重新核实。

1. 评审并合并此分支，确认PR/合并CI和干净 `main` 的精确SHA；稳定包不得从本功能分支直接发行。
2. 从该干净合并源码执行 `python scripts/build_release.py --tag bundle-v1.4.32 --output-dir <隔离发行目录>`。沿用总仓既有稳定目录和资产格式，只升级 Builder 1.1.31；其他四个Skill内容未改，发行时逐包摘要与上一稳定版核对，不另外升级或分发其他Skill安装。
3. 校验全部资产摘要、目录身份/版本和原更新器公开无登录新装、CURRENT及升级；发布不可变GitHub Release后，再核对两个账号指定Builder安装的未知改动、备份并同步，保留无关文件。
4. 回填真实合并、Release、公开安装与双账号同步证据，并更新组织wiki。缺一项就分别标待办，不以源码提交代替发行完成。

Skill 发布不自动迁移、改权、重建或部署任何现有系统；各线上能力是否已走网关由各层实际发布和验收证据决定。
