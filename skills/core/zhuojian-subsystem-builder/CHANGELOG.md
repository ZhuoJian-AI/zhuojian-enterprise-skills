# 更新记录

## 1.1.0 - 2026-09-11

- 将交接审计设为管理员初始化 ECS 的强制收尾，避免 Runtime 验收后遗漏服务器专属交接。
- 发现既有系统、数据通道、隧道、业务口径或其他服务器特例时，自动创建或更新独立交接 Skill，并以 `runtimeId` 为主、公网地址为兜底登记中央目录。
- 明确完成 PR、稳定 Release 和无缓存解析验证后才算发布；通用空白 ECS 不生成空壳 Skill，GitHub 写权限不足时必须报告未发布状态。

## 1.0.0 - 2026-09-11

- 将跨企业通用入口正式命名为 `zhuojian-subsystem-builder`，不再用 Alphabet 历史名称代表所有公司。
- 保留原 `aifabei-subsystem-builder` 作为同主版本兼容入口；旧用户再次调用时自动安装本 Skill，无需重新领取安装包。
- 企业身份以 ECS Runtime 的 `enterpriseKey + runtimeId` 为准；公司、服务器、既有系统和数据通道的特殊规则继续由中央目录匹配独立交接 Skill。
- 总仓库、现有 Alphabet Runtime、SaaS 接入契约 `2.4/2.5` 和业务负责人的首次登录方式均保持兼容。
