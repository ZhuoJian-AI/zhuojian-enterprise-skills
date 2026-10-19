# 一家公司一台业务服务器，多项目共用

任务 `COMPANY-SINGLE-SERVER-20261019`，主责为 `zhuojian-subsystem-builder`；部署 Skill 只同步选址入口及台账说明。用户纠正主改对象后，前一轮仅做过读取，没有把规则误写进其他 Skill。

## 结果与边界

新增 `references/company-server-policy.md`，由核心入口、管理员初始化及原生聚合引用。一家公司复用一台正式业务 ECS／现役 Runtime，多个 applicationSlug 同机部署，新增模块、域名、数据库或发布周期不另开服务器；容量不足先核对负载并评估现有主机升级。项目容器、数据、凭证、权限、域名、发布与回退各自保留。宿主机故障仍影响同机项目，不能把项目级隔离宣称成物理隔离。

共享 SaaS、统一模型网关、对象存储与 CI 保持原分工。历史多机如实登记，维护已有项目沿用当前主机；新项目没有指定承载主机时先明确归并目标，实际迁移另行授权。未修改 SaaS、Runtime、模板、Schema、更新器或公司交接 Skill，不购买、扩容、重启或退役服务器，契约保持 2.4/2.5。

## 发布范围

从已合并 PR73 的 main `4f98348bb1b8a38fad30d01c12c85fe1bd5e1eb7` 建独立分支，保留其全部内容。开始时 stable 为 core1.1.35；执行规定更新后为 CURRENT，已有三项企业交接 Skill 均 CURRENT。嵌入式 Python 的 managed updater 首次因脚本目录未入 sys.path 导入失败，在该次进程加入原 scripts 路径后执行成功，未修改更新器。

本轮版本为 core1.1.37；此前 core1.1.36 已独立发布为 bundle-v1.4.37 后才修改本轮版本，避免覆盖并行发布。版本断言随元数据更新，未改变其他测试行为。稳定版须待本 PR 合并、完整既有 CI 成功后从干净合并 main 构建下一个未占用 bundle，发布并核验匿名下载／原更新器安装；仅更新 main 不代表 stable 已更新。

## 验证与交付

按现有流程完成核心测试、quick_validate、受影响文档链接、YAML／JSON、秘密扫描和 diff 检查，真实结果与精确 PR/main、Release、包摘要、无登录安装、双账号同步写入最终 Wiki 回执，不预填成功。个人安装只同步本次授权文件，备份并核对并行变更，保留两账号的无关内容。

配套部署仓库为 `ZhuoJian-AI/zhuojian-server-deploy`；中央台账仅增加未来规划说明，24项名称、域名、IP、类型、归属和四机数量不变。不把本轮 Skill 发布称为历史服务器合并完成。
