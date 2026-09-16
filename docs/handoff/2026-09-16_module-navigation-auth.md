# 模块导航、权限策略与安全升级

- Core 已发布 1.1.5，契约仍兼容 2.4/2.5，不变更客户系统版本或授权。
- SaaS 提供系统与横向模块导航；嵌入模板保留首屏隐藏重复导航并采用 16px 紧凑内容。独立导航保留。
- 脚手架的通用记录操作声明模板已经实现的可配置范围。公共/个人业务应按实际需求实现，不按 CRUD 名称自动分类。
- `audit_permission_upgrade.py --current ... [--baseline ...]` 只读输出新增缺失策略错误、旧缺失升级清单、Action 变更。模块与页面拆分还须人工给出语义映射，禁止复制旧授权造成扩权。
- 已运行 core 全量测试初轮 223 passed、42 skipped、23 subtests passed；新增审计 4 项及模板生成 3 项通过。跳过不代表完成真实环境验收。
- 本轮只更新 SaaS 与通用 Skill；未部署业务子系统。企业专属八模块清单保存在 ai-platform 本轮交接，不进入通用规则。
- 从干净 main `2a058bfebb2a2d737cc57bd6446b5004e8f4368c`（PR #11）构建并发布 [bundle-v1.4.5](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.5)，9 个资产上传完成；公开无登录新安装 1.1.5、再次检查 current、本机 1.1.4 → 1.1.5 均通过。更新后已重读新规则。
- Release 非草稿、非 prerelease；版本资产包含校验信息，未覆盖旧包。GitHub API 的 immutable 标志为 false（仓库未启用 Release 不可变锁），不把版本化资产宣称为平台锁定不可变。
- SaaS 先完成 staging 保护发布及隔离管理员回归，随后发布 Skill；SaaS source `eafbff7`、manifest `12359b7`。下游未适配状态见 SaaS 同名交接与组织 wiki 通知。
