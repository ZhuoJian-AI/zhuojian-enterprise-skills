# 工作空间授权边界说明

1.1.6 区分 SaaS 工作空间默认只读与角色追加，以及仍按角色授权的业务页面／Action。新增 workspace-access 参考并在入口与平台契约链接；不改变契约版本、Runtime、模板或子系统代码。

验证：核心 `python -m pytest -q` 224 passed、41 skipped；quick_validate 通过。稳定 Release 与公开更新验证待完成，不以源代码版本号当作发布证明。
