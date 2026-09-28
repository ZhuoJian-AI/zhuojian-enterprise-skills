# MAINLAND-MIGRATION-20260928：迁移规范与企业交接候选

## 目标与授权

用户于 2026-09-28 明确授权把主 SaaS、两个 Alphabet 业务主机与相关 OSS 从香港迁往杭州，并同步两份 Skill、IP 和所有迁移依赖。本分支承担 Skill 契约和企业交接；真实主机、对象迁移、DNS 和稳定包发布由同一任务的迁移负责人协调。候选配置不代表目标已接管。

## 设计

- 通用 Builder 只增加跨主机/跨地域迁移规则，不写入 Alphabet 地址。不重建 `enterpriseKey/runtimeId`，不重新 provision 已接入 Runtime，不因地址变化改变应用 slug、员工权限、模块 ID、域名或契约版本。
- 迁移先保留源服务，目标容器和定时任务在隔离网络中验证。新旧主机不能以相同 Runtime 身份同时登记、接收发布、执行同步或写入。仅切 DNS 无法约束旧会话和后台任务，须有实际写入围栏。
- 普通 `configure-oss-gateway` 的现有 release 换 bucket/region 护栏继续有效。实际需要切换时，先取证真实 release、网关身份和对象引用，再实现匹配该状态的受控入口；不增加无证据的 `--force` 或声明式“已校验”跳过参数。
- OSS 保持对象键和应用前缀。完整清单、大小/哈希、删除标记、增量收口、源端只读和业务验收共同证明完整性；网关 CRUD 探针不能证明旧数据已复制。版本对象、历史签名/永久 URL、IMM/预览/Office、备份、RAM/CORS/生命周期必须单独盘点。
- 企业交接保留源地址并明确目标候选；中央目录增加已核实 Runtime ID 和杭州地址，未切换前不改操作脚本默认隧道。真实切换验证后同一变更补充生效时间和发布证据。

## 评审

- 产品/范围：迁移目标是同一 SaaS 与原有子系统继续服务；不借迁移重做界面，不迁企业 NAS 原件，不新增员工操作。Skill 发布、服务器部署、业务验证分开交付。
- 工程：源端健康服务与备份保留；最终数据库/对象增量在同一冻结窗口取得；迁移后新增数据存在时不能仅把 DNS 指回旧机。重试使用同一快照/作业标识并核实远端状态，防止双写、重建身份和覆盖未知对象。
- 设计/验收：没有新 UI。复验原有电脑端和手机端的登录、模块单击进入、iframe/助手、文件上传预览下载及跨租户拒绝；网络模拟和手机真机分开记录。运维配置采用“源/候选/已接管”明确状态，避免让后续 agent 把候选地址当已上线。

## 候选资源（上线状态待实际验收）

| 角色 | 源香港地址 | 杭州候选 | 身份 |
| --- | --- | --- | --- |
| 主 SaaS/Coolify/Registry/平台服务 | `47.243.201.63` | `47.114.61.74` | 平台现有资源标识保留 |
| 生产设计/企业文化/NAS | `8.218.208.205` | `47.97.90.161` | 已实测 `aifabei` / `aifabei-hk-01` |
| 商品动销/道讯 | `47.243.48.78` | `101.37.173.94` | `aifabei-hk-48`；企业键以源档案复核为准 |

`hk` 是既有身份的一部分，不能因为地理位置改变就重命名。主机类型 ECS/轻量不改变应用接入契约；实际实例 ID、地址、Runtime 档案与目标接管状态须由迁移负责人逐项复核。

## 发布与验证状态

已实现本地候选；未宣称 Skill 稳定包、运行时、主机、OSS 或 DNS 已发布。杭州企业 Bucket `alphabet-prod-hz-files-20260928` 已由迁移负责人实际创建，但复制、权限与切换验收独立进行。

专项 helper 为 `skills/core/zhuojian-subsystem-builder/assets/admin-runtime/host/migrate_oss_scope.py`，输入契约见随包 `references/oss-scope-candidate.md`。只操作源恢复后的隔离候选，不接触源机；Runtime CLI 锁、真实机身标识、完整 release 摘要、无新启动业务容器及停止的写任务是执行门槛。失败恢复 Runtime、网关配置、SQLite 身份库及应用令牌，使用原镜像 ID 重建并恢复每个应用私网。既有 `configure-oss-gateway` 完全未改。

独立审查：迁移负责人指出 compose 删除旧容器后失败可能阻塞回退，已把 stop 改为只接受明确的目标容器不存在状态；权限/daemon 故障继续拒绝，并补该故障与重跑测试。准备阶段 journal 生成前失败的目录不自动删除，保留人工检查证据。

验证环境：Windows / Python 3.12，隔离环境 `D:/Agent_Project/zhuojian-skills-mainland-tests-env`。专项 `python -m unittest discover -s tests/runtime_host -p test_migrate_oss_scope.py -q` 12 tests OK；最终完整 `python -m pytest -q -rs` 为 355 passed / 45 skipped / 1 dependency deprecation warning。跳过包括 POSIX 语义、模板只在生成项目执行的用例、缺 Playwright；不构成 Linux Docker/systemd/真实 OSS、手机真机或线上迁移通过。4 个改动 Skill 的 `quick_validate.py` 均通过，中央目录按两个 Runtime ID、四个新旧地址及主平台/未知 Runtime 隔离的 8 组检查通过；`git diff --check` 通过。

跨仓库影响：候选需协调部署规则、SaaS 平台存储网关和目标 Runtime；此处未授权或执行其他企业上线。三个 Alphabet 交接包仅为已有 Runtime 增加精确主机/身份选择与候选说明，旧地址保留；普通新旧契约 2.4/2.5 及历史兼容包不变。接管后须回填三个交接环境和隧道脚本的实际地址，再由协调者合并、稳定发布、验证公开安装/resolve与本机同步，并更新组织 wiki。
