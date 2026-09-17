# 手机网格与真实草稿检查候选

基线 `67754c9` / core 1.1.8。仅本地规范补丁，未发布新版稳定 Release、未更新业务 ECS。

正文及导航迁移参考明确桌面横向、手机四列自动换行（小于360px三列）；不要求滑动才能看全八模块。导航 Bridge 参考增加未编辑、编辑、保存、超时四种验收状态，禁止把超时当修改或靠固定 false 移除保护。

验证：core `python -m pytest -q` 230 passed / 41 skipped；quick_validate 通过；git diff --check 通过。跳过项不算运行时已验收。

SaaS 候选见 ai-platform 的 `docs/handoff/2026-09-17_mobile-grid-guard.md`。现有企业文化和商品动销页面仍缺少离开检查回应，需要业务负责人更新适配代码、验证真实表单后部署；仅更新 Skill 不会消除线上弹窗。

后续：稳定版本发布须按既有 clean merged main、版本、包验证及公开安装流程执行，本补丁不把未发布规范伪报为用户已自动更新。
