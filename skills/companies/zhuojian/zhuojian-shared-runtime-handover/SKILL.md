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
- 保留原 app、PostgreSQL、REST、REST proxy、migrate 服务、既有数据卷、网络和回退快照。原 Next.js 服务仍在运行；新 `native/` 源码存在不代表其已上线。
- 不覆盖共享执行器、代理、备份凭证或其他项目配置。不全局 prune，不按旧控制面名称删除活跃路由或业务资源。
- 新候选需要独立、受限 CI/SSH 发布身份和私有配置，不能把原发布账号改成任意命令/root。

## Lab 身份与业务边界

现有业务仍以原 Lab 表为真相源。SaaS 身份使用稳定用户 UUID；历史成员绑定来自私有核验回执，禁止按姓名匹配、复制密码或公开成员明细。实际工时与计划时间分开，不把计划回填为真实工作。

上线前盘点原入口、REST、MCP 与桌面客户端的全部员工业务路径和调用方。准备期间保留原服务和数据；正式切换必须统一当前 SaaS 授权并完成客户端迁移，不能让旧 Cookie/密码绕过停用和撤权。仅保护新路由不能报告统一身份完成。

原生候选目前覆盖计划/项目核心操作；任务树/甘特、使命/复盘以及旧客户端迁移仍待闭环。真实员工 SSO/撤权、双端/WebKit、模型可用性和生产发布分别验收；不把隔离测试或源码校验替代这些结果。

## 继续初始化

1. 读取当前档案并运行 `scripts/audit_runtime.py` 取得只读状态；它不是通用 doctor 的替身。
2. 按 Lab CODEOWNERS 审查认证、权限、迁移和 CI 候选；完成共享入口与登记发布器适配。发现通用工具暂不支持时保留准确 pending，不改默认安装器去接管共享机。
3. 备份并演练受限数据库角色、幂等迁移和稳定 ID 条件绑定；真实平台角色按已有职责配置，不能从职位名称推断授权。
4. 完成真正的 Runtime doctor、两个应用隔离/健康/存储/重建验收，以及员工端接受条件，再调整 `initialization.ready`。只有全部证据齐备才替换兼容入口。

本 Skill 不含 SSH、数据库、平台或模型秘密。长期访问复用已授权的本机 SSH 档案，不要求业务负责人再次提供密码。
