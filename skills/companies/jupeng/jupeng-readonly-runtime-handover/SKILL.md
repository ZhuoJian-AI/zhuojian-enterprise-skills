---
name: jupeng-readonly-runtime-handover
description: "飓鹏 ERP 只读底座在灼见杭州共享机的运行交接。按 jupeng-hz-shared-01 档案核对，保留 ERP 只读、稳定身份映射、共享代理和其他项目发布边界。"
---

# 飓鹏 ERP 只读接入

此交接用于已获授权的开发维护环境，补充通用子系统 Skill。此共享主机有多个企业 Runtime，不能使用默认 `/etc/zhuojian/runtime.json` 推断飓鹏身份。先读取 `/etc/zhuojian-runtimes/jupeng/runtime.json`：enterpriseKey 为 `jupeng`，runtimeId 为 `jupeng-hz-shared-01`，公网主机为 `47.114.61.74`。档案不匹配则停止本企业部署，核对目标；只按 IP 解析未提供企业时，需要先辨明档案。

## 发布边界

- 服务器 Git 真源为 `/srv/zhuojian/jupeng/repositories/jupeng-erp-readonly`，应用为 `jupeng-erp-readonly`。更新前检查现场 HEAD、工作树、release.json 和运行镜像的精确提交，保留别人的工作。
- 本企业共享主机适配入口为该仓库 `integration/shared_runtime.py`。`doctor` 检查本企业档案、配置和真实 ERP 只读依赖；`deploy --commit <完整SHA>` 只发布本应用。用不可变 Git 归档构建和测试，镜像标签与 OCI revision 必须等于源 SHA。回滚和发布只操作本企业拥有的容器与数据。
- 应用私有配置在 `/etc/zhuojian-runtimes/jupeng/apps/jupeng-erp-readonly/`；运行数据、部署回执、备份分别在本企业 `/srv/zhuojian/jupeng/` 下。凭证只在 root 私有文件复用，不复制到源码、Skill、网页或员工端。
- 使用既有 `zj-ingress-proxy` 和 `zhuojian-jupeng-frontend` 网络，不能安装标准 Nginx/direct-build Runtime 接管 80/443。不得覆盖默认灼见 Runtime 档案、原 Lab、其他项目 CI/SSH 发布器、共享代理、备份身份或卷；不得全局 prune。
- 本应用限制 0.5 CPU、384 MiB、96 PID，根文件系统只读。先检查实时总负载，不把专用应用预算当作共享主机总预算。
- 正式登记使用官方 `publish_subsystem.py`，显式传本企业 profile、release-file 和 app-env-file。新应用先 disabled，只有负责人已确认的员工才配置专用角色。登记和部署不等于真实员工登录通过。

## 数据与身份

原 ERP 保持独立生产系统；只读连接方式由私有访问档案提供。应用通过固定查询模板、字段白名单和只读事务查询，拒绝任意 SQL、保存、审批、删除、导出和附件下载。SSH 维护权限不能传给员工或统一助手。

SaaS 的固定用户 ID 通过服务端 `identity-map.json` 绑定 ERP 固定用户 ID。页面不能指定用户、角色或范围。实际访问为当前 SaaS 精确 Action 授权与绑定 ERP 用户的实时权限交集；缺失映射、停用、归档、未知策略及不能证明的组织继承均拒绝。ERP 管理员只有经负责人确认本人绑定且私有映射显式指定 `verified_admin_readonly` 才能查询已核对模块，仍无写入。

目录共 81 个模块、243 个只读 Action；敏感或未核实映射仍关闭。列表、详情和同条件记录数量共享服务。记录数量不是业务 KPI，不用数量冒充收入、利润等经营口径。字段和隐藏明细的限制以现场 catalog 与代码为准，不从底座角色绕过。

## 验收和维护

HTTPS 应用源为 `https://jupeng-erp-readonly.jupeng.staging.zhuojianai.com`，员工从底座获权入口进入。独立页面也必须有真实 SaaS SSO；不新增旧 ERP 密码登录通道。原 ERP 属于外部数据源，不宣称本次已迁移或接管其所有入口。

初始化证据在 `/srv/zhuojian/jupeng/initialization/`，两套无业务数据探针验证独立目录、重建保留、HTTPS 和底座登记；探针永不授予员工。现场 ready 状态、源码、源依赖、真实员工 SSO/查询/撤权和电脑/手机验收分别核查，不以旧说明替代实时结果。

会话数据是本地磁盘存储，没有业务文件上传或 OSS 迁移。备份包含本应用配置与源码，只能存放在受限位置；机外恢复点和自动监控须有实际回执才能称已完成。所有账号映射和用户明细只留私有核验材料，不进入此公共 Skill。
