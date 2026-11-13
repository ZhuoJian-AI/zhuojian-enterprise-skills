---
name: shengshi-qiancheng-runtime-handover
description: 盛世前程既有催费系统的源码、专用发布与数据定位交接。仅用于 shengshi-qiancheng-hz-01 或 118.31.111.74；现场状态优先。
---

# 盛世前程现有系统交接

这是可查询的环境事实，不是固定操作流程或额外授权。通用接入知识沿用 zhuojian-subsystem-builder；本机已有 ssqc-server-deploy 等项目说明继续保留，冲突按实际运行证据核对。

## 定位

目标企业 key 为 shengshi-qiancheng，Runtime key shengshi-qiancheng-hz-01，登记 UUID 1495fbb4-6f7e-49f1-887c-3f080f4a4424，目标公网118.31.111.74。Runtime 的 key 和登记 UUID 是同一目标的两种定位，均可匹配；不要因 doctor/配置权限不足重新初始化服务器。

催费与垫资管理 applicationSlug 为 ssqc-collection，入口 https://118-31-111-74.sslip.io/。项目原位置 /home/ssqc02/projects/ssqc-collection，实际接入代码在 direct-integration：ssqc_adapter.py、web/app.js、subsystem.json、publish.py。其他 subsystem 或 public-preview 目录不天然等于当前生效 UI。以当前进程、代理、Git 和发布指针辨认本次运行版本，不把本文历史路径当成当前发布指令。

既有专用发布器和冻结版本与标准 Runtime 并存；Runtime 已登记不等于该业务已由标准模块发布记录纳管。复用实际可用的原发布方式，是否迁移单独按任务判断。SSH 来源使用本机已获权访问档案，不从此包取得密码或私钥。

## 按问题查资料

[运行与数据线索](references/current-system.md)记录2026-11-13现场观察、风险位置和验收缺口；这些都是有日期的历史线索，后续 AI 先根据当前问题核实，不把旧故障断言成今天仍未修复。

当前工作进展与新运行版本记录回项目现有文档；稳定环境改变时再更新本交接。Skill 安装或更新不代表业务已经修复、发布、同步或本人验收。
