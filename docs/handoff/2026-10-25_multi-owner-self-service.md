# 多负责人自助开发与共享OSS企业隔离

本轮按用户确认保留同公司多个可信Codex的root维护能力，不新增逐负责人身份隔离、审批或管理前端必经步骤。其他公司仍独立企业服务器；员工业务权限不变。根分支`codex/multi-owner-skill-20261025`，原基线`5d6ffe63a37da49e77140f3fc4ec07b2f804696a`。

## 各层范围

- SaaS：精确事件契约比较与旧授权兼容证明、当前参与计划分页、手工精确路由查询/显式接管、原授权窗口事件恢复与请求回执。后端、worker及0088发布门禁在`ai-platform`独立工作树实现，不由Skill发布代替。
- Skill：整体业务确认后由AI配置并验收，移除平台管理员前端依赖；补服务器Git/工作树/发布基线、机外备份、共享两桶企业隔离及后续Codex接续。CLI只用当前Runtime本机凭据、固定路径与明确能力声明；恢复只接受精确事件清单、同请求摘要、未知只GET。
- Runtime：冻结Git归档构建、预期线上SHA与祖先检查、发布源码refs、维护及中断恢复、schema2的Git/data/config恢复包。用`--source-commit`发布任务提交，`publish_subsystem.py --use-running-release`登记真实容器及Manifest，公共工作区其他任务的dirty文件不被读取或发布。
- 原生模板：消费唯一性从全局event_id变为source/event/target-module；delivery别名保持业务结果与传输身份。已知标准旧SQLite表保留原记录迁移，自定义结构须专项迁移。
- 存储：共享业务桶与独立共享备份桶，企业/环境/应用前缀从可信Runtime派生；机外分片、精确版本整包校验、远端清单、隔离恢复及有限本地保留。旧桶/旧路径兼容，实际迁移另有受控步骤。

## 本地实际验证

Windows环境为`audit-2026-10-18/enterprise-notifications/skill-test-venv/Scripts/python.exe`。

- CLI基础、Runtime确认及自助发现/恢复：130 passed，1 Windows权限skip。
- publisher：22 passed，包括真实Git中他人未提交文件保留与缺少运行提交拒绝。
- 真实生成模板及其内部安全/恢复suite：父测试1 passed；覆盖跨模块消费、delivery替换、内容冲突、并发、旧表与旧hash回执。
- 整合首轮core：777 passed、63 skipped，44.22秒；此轮尚未包含存储代理后续提交及最终Linux证据。
- Runtime独立Windows集合：211 passed、1 POSIX skip，systemd沙箱路径followup另21项通过。真实Docker/Nginx/systemd切换未由这些mock测试证明。
- SaaS核心独立PostgreSQL：代理报告74 passed，提交`deb7f4bcd2e912db2d9f49610dea1045b2d2c9aa`；发布门禁仍待整合，不单独发布此提交。

## 尚未完成的交付状态

core候选1.1.46，稳定最新仍1.1.45/bundle-v1.4.48（本轮17时只读复核）。尚未推送/PR合并/稳定分发/双账号安装；Runtime未安装到47.97.90.161，SaaS未部署。最终Linux全套、独立审阅、公开包验证与两账号限定同步待完成。

Alphabet只读盘点证实当前独立业务桶`alphabet-prod-hz-files-20260928`；9仓库约428MiB、备份约5.1GiB，原备份没有Git和机外上传。本轮未搬文件、修改云端IAM、删除本地恢复点或联系旧101服务器。不能把共享前缀实现或机外上传mock测试称为现有企业数据已迁入共享桶。

初始云权限需在平台初始化上下文建立仅本企业前缀的身份，不能把全桶管理员Key复制到企业root服务器。既有文件迁移保持storageKey、完整比对后切换并保留原副本；NAS/道讯原件仍在企业内网，不在云端恢复包覆盖声明内。
