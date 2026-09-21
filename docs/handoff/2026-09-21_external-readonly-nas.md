# 外部 NAS 原件不迁移契约

## 责任和范围

子系统运行时负责按权限读取 NAS 与有界流式下载；SaaS 负责登录、实时授权、统一入口。Skill 本次只增加接入及验收规则，不修改/部署 SaaS 或既有三个业务系统。

Core 1.1.17 新增 references/external-readonly-files.md 并从入口与 object-storage 引用：NAS 原件不属于必须迁移到 Runtime 附件后端的文件，禁止云端正文缓存、无界扫描、跳过员工 ACL 或伪造 Artifact。正文 AI/Office 转换需另行明确数据流向。

Alphabet NAS handoff 1.0.1 同步只读、无云端正文存储及源端技术账户并不等于员工授权的要求；不复制公司凭证或业务资料。

## 验证

- canonical core `python -m pytest -q`：244 passed, 41 skipped。
- 两个变更 Skill 的 quick_validate：通过。
- `git diff --check`：通过（仅平台换行提示）。
- 安装与发布尚未完成，不将本分支更新宣称为用户已获得稳定版。

独立 NAS 子系统截至本文已在 8.218.208.205 部署登记 healthy（8f95f53）；真实员工全端验收尚在进行。SaaS 统一文件页没有随本 Skill 修改。
