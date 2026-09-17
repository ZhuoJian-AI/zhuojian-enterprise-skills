# 工作空间授权边界说明

1.1.6 区分 SaaS 工作空间默认只读与角色追加，以及仍按角色授权的业务页面／Action。新增 workspace-access 参考并在入口与平台契约链接；不改变契约版本、Runtime、模板或子系统代码。

验证：核心 `python -m pytest -q` 224 passed、41 skipped；quick_validate 通过。

source `ce5c28d81ca9d4baac36b1a795a88db8cc548a8c` 已发布稳定 bundle-v1.4.6，核心包 SHA256 `73aca4cd22de050ed6398375657fb67429205602c288cca56503c1de696eb27f`。公开无登录安装、再次检查 current、本机 1.1.5 → 1.1.6 升级通过。SaaS manifest `aac0c26` 已于 2026-09-17 14:24:24 CST 维护恢复，三个业务子系统不需为此变更部署，亦未代改其授权。
