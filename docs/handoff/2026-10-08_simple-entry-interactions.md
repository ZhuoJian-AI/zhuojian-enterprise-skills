# 原生光标与直接进入的默认约定

2026-10-08，用户要求将此前已在两账号本地安装中补齐的 Builder 规则与模板推送至官方源码。开发基于最新 origin/main `52a4e678c4ccc53663a472236fd78c29f3bd3b56` 的独立工作树，不将旧安装版覆盖新版源码。

## 范围与责任

- SKILL.md：默认原生鼠标光标、静态入口和单次正常激活。
- references/platform-contract.md：公共外壳由 SaaS 负责，内部业务页面由子系统负责；保留键盘焦点、触摸滚动/取消保护和授权入口。
- assets/native-subsystem-template/AGENTS.md：后续生成项目采用相同默认。
- 保留已确认的图片、丝带背景、业务规则及独立的 assistant-presence 语义锚点提示；不修改运行脚本、Schema、SSO、权限或契约版本。

## 验证与发布边界

检查三处新增文本与两个账号的已授权本地补丁一致；去掉新增文本后与最新 Git 基线一致。Skill 快速校验、Markdown 相对文件链接及 diff 检查通过。未修改代码，不重复运行全量业务/浏览器测试；本次不主张桌面、手机真机或业务线上验收完成。

本次仅推送 feature branch 并创建普通 PR；不合并 main、不发布稳定 Release、不执行 SaaS、Runtime 或子系统部署。skillVersion 保持现有 1.1.29；稳定更新器仍只读取已发布的不可变 Release，因此源码推送不会自动升级其他安装。

上述为第一轮推送状态。用户随后明确授权合并并发布，现补充 core 1.1.30 版本与同版本更新记录，准备 bundle-v1.4.31。正式发布须在本 PR 完整测试通过并合并后，使用干净合并源码构建包；公开下载、安装校验与双账号本地差异核对另记真实回执，不能以本段当作已发布证据。

## 跨仓库影响

组织 wiki 的 zhuojian-enterprise-skills 卡片已核查。本次仅改变未来界面的默认约定及生成模板中的开发说明，不改变模板运行代码或对外协议；现有项目不会自动删除已装载的脚本。SaaS 与 Alphabet 的生产协同、企业文化、商品动销和公司共享盘有本轮独立代码修复、推送与未部署记录；其他下游在后续获授权改造时核查，无需因本次文档推送强制重部署。未合并、发布或部署，尚不产生发布后的下游通知。

## 正式发布补充（2026-10-08，以本节为准）

- 用户随后明确授权合并部署。源码 [PR #62](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/pull/62) 已合并至 `9a1fe96f2a78eca57e94fadd74311c5b10281b35`，从该干净合并源码构建 **core 1.1.30 / bundle-v1.4.31**，稳定 Release 已正式发布；前文「不合并/未发布」是实施时检查点。
- 完整测试 **522 passed / 53 skipped**、quick_validate、diff 检查通过；[PR head CI 37755612354](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/actions/runs/37755612354) 在 `12d383f75026e6f3eeaa83d291163afab73ba8b0` 成功。53 项跳过含平台限定和原始模板占位检查，生成项目子测试已运行；不将 skips 报作通过。
- 九个本地 Release 资产验证通过，另外四个 Skill ZIP 与上一稳定 bundle 完全相同；随后 **9/9 匿名公开资产 SHA-256** 与冻结本地产物匹配。公开 bootstrap 与 ZIP 内原更新器同字节，没有修改 transport、校验或 TLS。
- 原更新器默认稳定通道全新安装输出 `SKILL_UPDATED installed 1.1.30`，4.797 秒。首次 CURRENT 遇 EOF，被原脚本报告 warning 且退出码 0，**不计该轮通过**；一次有界重试输出 `SKILL_UPDATE_CURRENT 1.1.30`，1.453 秒。新装 **156/156** 文件与公开 ZIP 逐字节一致、额外文件 0，本验收跳过 0、进程超时 0。证据：`D:/Agent_Project/subsystem-simple-cursor-20261008/skill-public-install-v1.4.31/ACCEPTANCE.md` 及同目录 JSON 回执。
- 两账号事先完整备份，使用原更新器升级：codex02 **1.1.25→1.1.30**（初次 SSL EOF 保留旧本地目录，第二次成功），王鑫涛 **1.1.29→1.1.30**；之后两边 CURRENT 均成功。各 **156/156** 文件与公开 ZIP 同字节、缺失/差异/额外文件均 0。证据：`D:/Agent_Project/subsystem-simple-cursor-20261008/skill-sync-evidence/builder-stable-installed-1.1.30.json`。保留真实网络失败边界，不宣称默认网络永不失败。
- 本次仅更新 Builder 默认交互及开发说明，保持运行脚本、Schema、SSO、权限、contractRevision 2.4/2.5 和其他四个 Skill 的版本。SaaS 公共入口与四个 Alphabet 子系统本轮有各自真实部署/验收，Skill Release 不代替其运行态证据；实体手机和既有业务缺陷仍保留边界。
