# 多系统对接 Skill 流程

## 范围与责任

本次主责为Skill：core1.1.45补充三个、四个或本企业当前明确全部应用/模块的整体业务确认、自动拆分配置、依赖恢复和整链验收。沿用真实SaaS/CLI的单事件计划最多两应用、八精确边与连通限制；没有新增批量API或事务。业务实现仍由各子系统负责，本次不发布SaaS、Runtime或企业应用，不据此声称Alphabet已业务打通。

新增 `references/multi-system-integration.md`，从SKILL及原cross-system参考显式路由。整体清单和计划映射保存在本地交接，`docs/ai-delivery.json`按既有证据字段关联，不改变Manifest、Schema、2.4/2.5契约或运行时调度。

负责人在Codex确认精确整体范围一次，开发AI复用获权Runtime逐计划执行；不要求逐项操作管理员前端。新增系统、模块、方向或扩大数据/操作/期限需确认差异。原有关系先核实复用，禁止冲突时换请求ID；部分失败和未知先回读，成功部分不重做。整体方案不产生跨计划原子提交、数据自动回滚或员工越权。撤销按计划停用路由，保留已完成业务数据和进行中写入边界。

## 审阅与检查

- 独立审阅已将CLI及SaaS源限制逐条核对；三系统顺序、四系统分支汇合、全部含未获权、partial/unknown/revoke场景推演无阻断问题。业务对象映射、转换产物校验与参与端未知状态读回建议已纳入。
- `quick_validate.py skills/core/zhuojian-subsystem-builder`通过。
- 第一轮本机完整core为728通过、57跳过、1失败：既有版本断言仍固定1.1.44。已同步为本次1.1.45后重跑；不修改运行时逻辑。
- 最终本机完整core为729通过、57跳过、1个既有依赖弃用警告，耗时42.73秒；日志在本机审计目录 `multi-system-integration/local-core-tests.log`。四份相关Markdown共48个本地链接与`git diff --check`通过。PR/main CI、公开资产及原更新器安装验证、两账号限定同步结果在发布完成后追加实际回执，不提前标成功。

本机测试解释器：既有 `skill-test-venv` Python3.12；测试跳过及警告以原始日志为准，不能据静态规范或模拟验收关闭企业实际业务/真机缺口。

## 发布与同步

目标公开仓库：`ZhuoJian-AI/zhuojian-enterprise-skills`。从reviewed PR的干净合并main构建core1.1.45稳定bundle；其他五个Skill及bootstrap updater仅在源码未变证明后复用上一稳定包字节。源merge、Release、公开十资产与latest、core fresh/44升级/CURRENT、legacy入口、selector与个人同步分别留实际结果。

个人同步只涉及core六路径：`SKILL.md`、`CHANGELOG.md`、`skill-version.json`、`references/cross-system-integration.md`、新增 `references/multi-system-integration.md`、`tests/test_contract_versions.py`。分别先备份与核对预期摘要，再原子写入及读回；两账号范围外文件保持。企业专属Skill、部署Skill、凭据及账号配置无本次变更；不推定其他负责人电脑已经更新。

## 实际发布与同步结果

- [PR91](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/pull/91)正常合并，精确打包source为`217ddca7bb218d794d4ae6f0a1ec75281f8b94e4`。[PR CI40165174623](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/actions/runs/40165174623)与[main CI40165361979](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/actions/runs/40165361979)均成功，各729通过、57跳过、1个既有依赖警告。
- [bundle-v1.4.48](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.48)（Release ID423165869）于2026-10-25 13:25:58 CST公开。冻结十资产均与供应商上传digest、匿名下载大小/SHA匹配；四latest入口和tag source一致。供应商返回immutable=false，原样记录，未修改仓库设置或其他已发布Release。
- 从匿名实际下载的原更新器完成core1.1.45全新安装、1.1.44→1.1.45升级及各自CURRENT；两隔离安装均171文件与公开ZIP逐字节一致。legacy1.2.0安装/CURRENT为11文件一致，原managed目录加载器及八selector通过。其他五ZIP与独立bootstrap保留bundle47的精确原字节，未变企业交接/共享包版本。
- `r48pub/public.actual.json`为公开验收实际回执。`r48sync-apply/result.json`记录两个本机账号各六路径限定同步成功，备份、整树CAS、原子写入和读回完成，两账号范围外字节保持；这不推定其他负责人电脑已更新。

本次交付完成的是Skill稳定流程。具体企业的真实模块处理、精确授权配置、源/目标业务读回及电脑/手机页面仍由该企业获权Codex按需求实施和验收；本次没有SaaS、Runtime或业务系统发布，不把配置规范或安装成功称为Alphabet业务已经打通。此后docs-only回执不改变上述已发布tag/source或包内容。
