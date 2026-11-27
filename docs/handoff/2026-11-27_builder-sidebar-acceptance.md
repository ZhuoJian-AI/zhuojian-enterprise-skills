# Builder 1.1.70 员工工作台导航验收

发布前核对候选 Manifest 的应用、模块和页面层级，明确员工侧栏的展开或直达结果。实际员工入口逐项核对模块显示、跳转和角色可见性。公共侧栏、移动端抽屉和 iframe 内部页签的分工与当前工作台对齐。

仅修改指导和 Skill 版本。接入契约 2.4、2.5、源码模板、Runtime 和业务子系统行为继续沿用。

本机运行 `python -m pytest tests/test_contract_versions.py tests/test_workflow_guidance.py tests/test_update_skill.py -q` 通过 79 项，Skill 校验及 diff 检查通过。公司 CI、正式分发及双宿主加载分别核验。
