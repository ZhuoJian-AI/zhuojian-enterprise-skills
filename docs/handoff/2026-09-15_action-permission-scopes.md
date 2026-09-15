# 按操作范围契约同步

SaaS 兼容实现先发布，source `2f527f5`、manifest `d4bfb4e`；本次 Skill 扩展保持契约 2.4/2.5，不修改业务服务器或真实授权。

正文、契约参考、模板规则、Manifest Schema 与语义校验新增可选 permissionPolicy。固定本人不可扩大，公开模式仅 query，管理范围限定声明集合；旧记录不因扩展自动放宽。新增 13 项聚焦检查已通过。完整核心测试 202 passed、41 skipped；跳过项为既有 Windows POSIX 检查和须生成项目后执行的模板路由集成测试，本次未改运行模板代码。quick_validate 通过。稳定发布和无缓存下载证据待补。

这是开发契约交付，不代表任何下游系统已经完成运行时隔离验收。后续企业文化修改与双员工验收单独记录。

稳定发布完成：PR #7，合并 source `4917deb1a947820593ce31685c9de9b62cc32404`，Release `bundle-v1.4.2`，核心 Skill `1.1.2`。干净合并提交构建；核心压缩包 SHA-256 `c40da5567be140159483f91bfc9e69d78411b60e2a995eb062615b93563f3c4e`。清除命令进程 GitHub Token 后，官方更新器全新目录安装返回 `SKILL_UPDATED installed 1.1.2`；本机缓存经更新器由 1.1.1 升至 1.1.2。其他企业交接 Skills 版本未变。
