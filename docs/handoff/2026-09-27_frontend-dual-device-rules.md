# 电脑端与手机端双端交付规范

- 任务：`FRONTEND-DUAL-DEVICE-RULES-20260927`，执行者 Codex。
- 源码基线：`5624ca4`；分支 `codex/frontend-dual-device-rules-20260927`。
- 用户明确要求前端电脑端、手机端分别设计与交付；本次仅调整 Skill 规范，不修改 Runtime、SaaS 或业务系统实现。

## 修改范围

1. 总 Skill 入口明确两套界面方案和分别预览/验收的要求。
2. `references/platform-contract.md` 替换“不开发第二套手机版”与强制“同一业务 DOM”的旧限制，明确共享数据/权限/业务逻辑/草稿，允许各端专用视图；保留平板、连续宽度、可访问性、全部 Manifest 页及嵌入/独立入口验收。
3. `assets/native-subsystem-template/AGENTS.md` 同步要求，保证新生成项目的开发入口不会继续指向旧限制。
4. 三份文档同步到用户指定的本机已安装 Skill；原文件在工作区留有备份，同步前核对安装副本与源码基线一致。

没有修改 `skillVersion`、接入契约 2.4/2.5、Schema、校验器或模板运行代码。当前安装包版本仍为 1.1.22，新增规范属于本地文档修订，不冒充已经发布的新稳定版本。后续中央稳定发布必须另行更新版本/CHANGELOG、合并、完整测试、打包和公开安装验收；新版安装可能覆盖本地文档，中央变更需要随正式版本发布。

## 验证

- `python <skill-creator>/scripts/quick_validate.py skills/core/zhuojian-subsystem-builder`：通过。
- 对本机安装目录运行同一快速校验：通过。
- 三份源码文档与本机文档逐一比对一致；41 个相对链接存在，UTF-8 无 BOM/替换字符。
- 旧冲突语句搜索无匹配；`git diff --check` 通过。
- 快速校验器最初缺少 PyYAML，后在任务临时目录安装 PyYAML 6.0.3 并通过 `PYTHONPATH` 仅供本次校验使用；未修改系统 Python 或项目依赖。
- 只修改 Markdown，不新增重复实现的测试、不重跑未受影响的 Runtime/模板功能套件；没有运行浏览器、真机或业务验收，不声明现有系统已完成双端适配。

## 责任与发布边界

Skill 主责是开发约束和验收契约；SaaS 负责公共外壳双端，子系统负责业务页面双端。此次仓库文档候选与本机规则已更新，稳定 Release 尚未发布。没有修改任何企业 Manifest、员工授权或业务页面，也没有部署 SaaS、企业 ECS 或 Runtime。既有子系统无需仅因文档更新重新部署，后续相关页面改动需按新规则检查并交付双端。
