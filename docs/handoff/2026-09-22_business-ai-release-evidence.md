# 业务提效 Skill 稳定发布证据

任务 BUSINESS-AI-DELIVERY-20260922，执行 Codex。设计、适用边界和本地测试见 [实施交接](2026-09-22_business-ai-delivery.md)。

## 发布事实

- [PR #33](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/pull/33) 已合并；源码 `2422d07508465dc9c6b11eade5cfff982e137cb9`，与独立审查和本地测试的代码树相同。
- [PR 云端回归](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/actions/runs/35676368703) 与 [主线回归](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/actions/runs/35676601914) 均成功，分别 274 passed / 41 skipped / 1 warning；主线用时 28.43 秒。Draft 阶段的重复运行被跳过/取消，不算测试通过证据。
- 从干净的上述主线提交运行 `python scripts/build_release.py --tag bundle-v1.4.18 --output-dir <临时资产目录>`；5 个压缩包摘要均与 catalog 相符，共 9 个发布资产。
- [bundle-v1.4.18](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.18) 于 2026-09-22 09:44:48 北京时间发布。核心 1.1.18，其余版本不变；未覆盖任何旧 Release。
- 核心压缩包 506731 字节、137 个条目；SHA-256 `5e9e31203e3ad5925e48222da77415164e99fb336e10716392b2d2104d8425aa`，GitHub 资产摘要与本地一致。

## 公开安装、本机更新与网络限制

默认 Python urllib 更新器通过本机既有代理读取公开稳定入口时连续 3 次 `Remote end closed connection without response`，未成功安装；每次失败均保留旧版。无 GitHub 登录过期证据，不改代理订阅、全局 Git 配置或 TLS 校验。

同一代理上的无登录 curl 对入口返回 HTTP 200。使用一次性传输适配将原更新器的 `read_url` 换为 curl HTTPS 读取；仍调用原 `run_update`，保留仓库/Skill/稳定版本验证、大小上限、SHA-256、压缩路径/链接检查、更新记录检查与原子替换，不使用 `allow_test_url`，也不改已发布更新器源码。

结果：

- 从公开 latest 入口安装到全新隔离目录：`installed None -> 1.1.18`。
- 从同一公开入口重复检查：`current 1.1.18 -> 1.1.18`。
- 本机正式 Skill 在先备份旧目录后更新：`updated 1.1.17 -> 1.1.18`；本机与公开安装的 SKILL 内容摘要一致，已读取新版版本、更新记录和 Skill 正文，核心 quick_validate 通过。

**证据边界**：公开下载和原更新器校验/安装路径通过；默认 urllib 自动更新的本机代理兼容问题尚未验证恢复，不能写成默认自动更新链路已通过。网络不通的其他负责人不会被强制覆盖，仍沿用旧版；其他人的电脑未在本轮远程更新。

## 跨仓库通知

- [生产协同 #44](https://github.com/ZhuoJian-AI/garment-production-collaboration/issues/44)、[COA #168](https://github.com/ZhuoJian-AI/coa/issues/168)、[旧 Builder #20](https://github.com/ZhuoJian-AI/aifabei-subsystem-builder/issues/20)：下一次新增/实质改造执行新规范；纯维护不全量迁移，不紧急重部署，不删除独立产品合同能力。
- [模块需求独立源 #1](https://github.com/ZhuoJian-AI/zhuojian-module-requirements/issues/1)：随包副本已更新，独立仓库未改，须核对来源差异后同步。
- [SaaS #356](https://github.com/ZhuoJian-AI/ai-platform/issues/356)：能力核对、主动触发/委托、跨层回执的待核实需求；已提交不等于已受理或实现，不授权无人值守写入。
- 组织 Wiki 已推送 [77628cd](https://github.com/ZhuoJian-AI/zhuojian-llm-wiki/commit/77628cd49c9f55eea2ada3f4e1dc2cec5ab7d1fa)，更新本仓与五个关联仓库卡片中的责任/Issue 引用；见该仓 `docs/handoff/2026-09-22_0949_wiki_business-ai-delivery.md`。

## 未做与责任

主责 Skill：规则、随包需求、开工模板和本地校验器已提交、推送、发布，并完成上述安装验证。附属中文名字的通用校验限制及业务情景评估局限沿用实施交接说明。

SaaS、Runtime、企业文化、生产协同、商品动销均未改代码、改权限或部署。本轮未执行真实业务数据读写、线上端到端、离线任务触发或企业效率实测。现有三个子系统不会因 Skill 发布自动变得主动；后续按具体业务流程改造，涉及平台新增能力时先实现 SaaS，再同步真实契约与需要的子系统。
