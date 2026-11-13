---
name: zhuojian-shared-runtime-handover
description: "灼见杭州共享 Runtime 的初始化和 Lab 原生接入交接。仅匹配 zhuojian-hz-shared-01 或 47.114.61.74；保留同机独立入口、CI/SSH 发布器、原 Lab 服务和数据，区分身份登记与完整初始化。"
---

# 灼见共享 Runtime 与 Lab

本交接补充总 Skill，不替代其身份、权限、确认和验收契约。先读服务器当前非敏感 Runtime 档案；企业应为 `zhuojian`，`runtimeId` 应为 `zhuojian-hz-shared-01`。不按公司名把本交接用于其他主机。

## 2026-10-22 核验状态

Runtime 企业身份已登记；凭证在 root 受限目录，本地存储探针通过。档案明确 `initialization.ready=false`、`registered-host-adapter-pending`，完整初始化未完成。没有部署 Lab 原生候选、应用生产迁移或更改员工密码。以后先读现场状态，不把本记录当成永久进度。

主机是正在服务多个项目的共享机。80/443 已由独立 Traefik 入口占用；Nginx 和通用 `zhuojian-runtime` 尚未安装。**不得直接运行标准 Nginx/direct-build 安装器来补齐检查，也不得伪造 doctor 通过。** 需要保留现有入口与项目发布边界的共享主机适配，再完成备份与两个独立最小应用验收。

## 发布与不可触碰的资源

- GitHub 源码 `ZhuoJian-AI/lab`；生产入口 `https://lab.zhuojianai.com`，原 REST 入口 `https://lab-rest.zhuojianai.com`。
- 原 Lab 走已登记的 `lab` CI/项目 SSH 发布器。先读取最新 `灼见服务器部署` 规则和 Lab 的 AGENTS、CODEOWNERS、TASKS、部署登记与交接；不使用直接 Compose、原控制面或容器内手改绕过原发布门槛。
- 保留原 app、PostgreSQL、REST、REST proxy、migrate 服务、既有数据卷、网络和回退快照。原 Next.js 服务仍在运行并须保留；原生应用已另经 lab-native 专用发布器上线。各自的实际版本与健康状态分别核对，不因源码存在断言已部署。
- 不覆盖共享执行器、代理、备份凭证或其他项目配置。不全局 prune，不按旧控制面名称删除活跃路由或业务资源。
- 新候选需要独立、受限 CI/SSH 发布身份和私有配置，不能把原发布账号改成任意命令/root。

## Lab 身份与业务边界

现有业务仍以原 Lab 表为真相源。SaaS 身份使用稳定用户 UUID；历史成员绑定来自私有核验回执，禁止按姓名匹配、复制密码或公开成员明细。实际工时与计划时间分开，不把计划回填为真实工作。

SaaS 员工入口消费当前平台企业、角色/Action 与范围，已有可信稳定绑定继续承接旧数据；无绑定的新员工可幂等建立无密码业务人员资料，不需要第二份本地管理员或成员白名单。本地历史角色、旧账号和原独立入口保留其原授权边界；SaaS 通道撤权不能回退旧 Cookie/密码，新旧通道也不合并权限。C 端/附属用户可独立存在，无需自动成为企业员工。

上述 2026-10-22 快照不代表当前原生部署状态。后续原生计划、项目与复盘已有独立发布记录；具体覆盖和未测功能以当前项目交接为准。真实员工 SSO/撤权、双端/WebKit、模型可用性和生产发布分别验收；不把隔离测试或源码校验替代这些结果。

## 按现场状态接续

scripts/audit_runtime.py 提供只读线索，不替代通用 doctor。共享机的 initialization.ready 与已登记原生应用的独立基础证明分别核对，不因历史 ready=false 重新接管 80/443 或推翻已验证发布。原生服务使用独立 lab-native 受限 SSH 发布身份、当前 CI 制品和受保护发布器；原 lab 身份不代替它，也不开放任意 root 命令。

根据本次问题选择有关的源码、CODEOWNERS、回执、备份、稳定绑定或真实员工证据；已有证明可复用，缺口按实际结果处理，不要求每次维护重新初始化或固定执行一遍迁移。人员主档来源、SaaS 对应和子系统业务资料是不同证据；当前尚未配置的原通讯录连接不能冒称已同步。

本 Skill 不含 SSH、数据库、平台或模型秘密。长期访问复用已授权的本机 SSH 档案，不要求业务负责人再次提供密码。
