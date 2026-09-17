# 手机网格与真实草稿检查候选

基线 `67754c9` / core 1.1.8。已发布 core 1.1.9 / bundle-v1.4.9；source `de4cb48f3e6e59e4180644b8b1f60d7fd2c93639`，PR #19。未更新业务 ECS。

正文及导航迁移参考明确桌面横向、手机四列自动换行（小于360px三列）；不要求滑动才能看全八模块。导航 Bridge 参考增加未编辑、编辑、保存、超时四种验收状态，禁止把超时当修改或靠固定 false 移除保护。

验证：core `python -m pytest -q` 230 passed / 41 skipped；quick_validate 通过；git diff --check 通过。跳过项不算运行时已验收。

SaaS 候选见 ai-platform 的 `docs/handoff/2026-09-17_mobile-grid-guard.md`。现有企业文化和商品动销页面仍缺少离开检查回应，需要业务负责人更新适配代码、验证真实表单后部署；仅更新 Skill 不会消除线上弹窗。

发布验证：从干净合并提交生成不可变包与稳定 catalog；公开无登录全新安装得到 1.1.9，重复检查 current；本机 1.1.8→1.1.9 成功。负责人机器须在联网调用 Skill 时完成更新，不能声称所有机器已更新。
