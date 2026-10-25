# 多负责人自助开发与共享OSS企业隔离

本轮按用户确认保留同公司多个可信Codex的root维护能力，不新增逐负责人身份隔离、审批或管理前端必经步骤。其他公司仍独立企业服务器；员工业务权限不变。根分支`codex/multi-owner-skill-20261025`，原基线`5d6ffe63a37da49e77140f3fc4ec07b2f804696a`。

## 各层范围

- SaaS：精确事件契约比较与旧授权兼容证明、当前参与计划分页、手工精确路由查询/显式接管、原授权窗口事件恢复与请求回执。后端、worker及0088发布门禁在`ai-platform`独立工作树实现，不由Skill发布代替。
- Skill：整体业务确认后由AI配置并验收，移除平台管理员前端依赖；补服务器Git/工作树/发布基线、机外备份、共享两桶企业隔离及后续Codex接续。CLI只用当前Runtime本机凭据、固定路径与明确能力声明；恢复只接受精确事件清单、同请求摘要、未知只GET。
- Runtime：冻结Git归档构建、预期线上SHA与祖先检查、发布源码refs、维护及中断恢复、schema2的Git/data/config恢复包。用`--source-commit`发布任务提交，`publish_subsystem.py --use-running-release`登记真实容器及Manifest，公共工作区其他任务的dirty文件不被读取或发布。
- 原生模板：消费唯一性从全局event_id变为source/event/target-module；delivery别名保持业务结果与传输身份。已知标准旧SQLite表保留原记录迁移，自定义结构须专项迁移。
- 存储：共享业务桶与独立共享备份桶，企业/环境/应用前缀从可信Runtime派生；机外分片、精确版本整包校验、远端清单、隔离恢复及有限本地保留。旧桶/旧路径兼容，实际迁移另有受控步骤。

## 实际验证与独立审查

- CLI 130 passed / 1 Windows POSIX skip；publisher 22 passed，包含真实 Git dirty 工作区保留；真实生成模板及其内部安全/恢复 suite 通过，覆盖旧表/hash 回执、并发和跨模块幂等。
- 合并源码 `2710a5714065dc70ff772cd1e37d9cf75b5b4005` 的 Linux 完整 core **814 passed / 64 skipped**，仓库根兼容入口 4 passed，host assets 43 passed。64 skips 为 59 项需生成应用上下文、4 项该镜像无 Node、1 项无 Playwright；不把这些算通过。gateway 47 项包含在 core 内，不重复计数。
- 独立复核修复旧 Runtime 0600/0640/0644 非敏感 metadata 与 OSS 凭据 0600 的混用，并保留非 root、可写权限、符号链接拒绝。最终代码 `5a9831606cee8919bab9493f74e54252d8936775` 增量 Linux：backup+installer **40 passed**、gateway **60 passed**，均零跳过；包括 13 项真实 POSIX gateway 用例，以及绝对配置路径、完整备份来源和 metadata 模式增量。
- CI 主机真实 systemd ProtectSystem/PrivateTmp 沙箱中，源码写入被拒绝；Git bundle verify、独立 clone、tar 全读回与维护失败恢复通过。另用缓存 Nginx 容器及隔离证书验证生成维护配置。Docker stop/start、平台 HTTP 和业务健康边界是替身；此结果不是线上发布或实际应用数据库恢复证明。
- 真实 CLI urllib → SaaS ASGI → 隔离 PostgreSQL 联合 2 passed，覆盖分页/原路由 ID 接管、中文摘要、POST 已提交而响应丢失时只 GET 对账。SaaS 独立 PG 74 passed、Alembic/增量 18 passed、native gates 352 passed / 2 Docker opt-in skips、Control 229 passed、readiness 14 passed、CI profile 24 passed。SaaS 独立复核发现恢复接口缺逐 edge 所有权校验，修复与最终组合结果以该仓交接为准，不能提前称通过。
- Skill quick_validate 通过。源码审查覆盖模板保留旧数据、逻辑/传输幂等、API 未知结果、备份 manifest 接合；未留已确认的 Skill 阻断。`git diff --check` 通过。

实际日志位于任务本机 `audit-2026-10-25/multi-owner-self-service-fix/`。systemd 任务目录已核身份后清理，测试镜像保留复用；其他代理测试资源以各自 cleanup 回执为准。无真实云 OSS 上传/恢复、员工页面或手机真机验证。

## 交付状态与上线范围

core 候选 **1.1.46**，稳定最新仍 **1.1.45 / bundle-v1.4.48**（本轮 17 时只读复核）。代码已提交、测试并独立审查；PR、稳定分发与两账号同步由根任务收尾并另记实际结果。Skill 发布不会自动安装 Runtime 或部署 SaaS。

需要分别交付：`ZhuoJian-AI/ai-platform` 的 0088 后端/worker/Control 与 root 发布器；`ZhuoJian-AI/zhuojian-enterprise-skills` 的 core 分发；47.97.90.161 上受控 Runtime/gateway/backup helper 更新及共享桶初始化/实际恢复验证。现有业务系统只在后续获权改动中适配新模板；本轮不自动重建九个系统，不修改员工权限。SaaS/Runtime 尚未部署，云 IAM 与 bucket 尚未修改，实际迁移另以完整逐对象核对和回退副本验收。

Alphabet只读盘点证实当前独立业务桶`alphabet-prod-hz-files-20260928`；9仓库约428MiB、备份约5.1GiB，原备份没有Git和机外上传。本轮未搬文件、修改云端IAM、删除本地恢复点或联系旧101服务器。不能把共享前缀实现或机外上传mock测试称为现有企业数据已迁入共享桶。

初始云权限需在平台初始化上下文建立仅本企业前缀的身份，不能把全桶管理员Key复制到企业root服务器。既有文件迁移保持storageKey、完整比对后切换并保留原副本；NAS/道讯原件仍在企业内网，不在云端恢复包覆盖声明内。
