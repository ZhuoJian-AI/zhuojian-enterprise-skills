# Root 审批补充内网的持续维护

本补丁归 Runtime helper 与 Skill 接入约束；SaaS、子系统业务源码和 SDK 保持。它补齐迁入应用后续正常 deploy/rollback 丢失第二网络的问题，适用于维护方明确批准的已有 internal bridge；原主网和没有记录的应用沿用原行为。具体企业网络 ID 不进入通用 Skill。

从干净 `1c29665014ef7461c118f0380fff93ea6d63aa51` 在独立本地分支实施。审批仅取 `/etc/zhuojian/network-attachments/<slug>.json`，root700/600、无符号链接与共享写权限，严格绑定 slug、Runtime alias、org、环境、企业及最多两个真实网络名/ID。业务 metadata 不能选择网络。

发布/回滚停止旧版前验证，创建新容器后按精确 ID 连接补充网络，核对后才启动；连接失败保持 stopped，后续外层发布仍执行既有恢复旧版协议。记录/网络不匹配时在停止旧版前拒绝。SDK 原字节不变，版本仍为尚未发布的 1.1.44。

本地验证：便携 Python 3.13 运行 `tests/runtime_host/test_runtime_network_attachments.py -v`，11 项通过。覆盖无记录原路径、正确双网顺序、连接失败不启动/删容器、部署/回滚预检、原生 rollback 实际进入 create/connect/start 路径、root/权限/符号链接元数据、重复字段、跨身份和已重建/外部网络拒绝。另运行 `tests/runtime_host/test_runtime_admin.py RuntimeHostTests.test_oss_container_joins_private_network_and_uses_second_env_file -v`，1 项通过。未重跑无关的 94 项历史套件。本机便携解释器无 PyYAML/pytest，quick_validate 与两项原 pytest 版本切换协议回归待独立隔离 CI；没有用模拟解析冒充通过。

尚未安装生产 helper、创建实际审批记录、执行真实普通部署/回滚、推送 GitHub、发布稳定包或同步个人 Skill。Root 在本次冻结导入脚本全部执行后独立安排安装，避免其旧 helper SHA 固定值冲突。
