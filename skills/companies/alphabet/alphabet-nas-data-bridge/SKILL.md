---
name: alphabet-nas-data-bridge
description: "在 Alphabet 的 8.218.208.205 或 47.243.48.78 ECS 上，经群晖 NAS 反向隧道只读浏览企业共享资料，并把选定资料接入灼见 SaaS 子系统。用户提到 10.0.0.33、NAS、共享盘、000、AI、outshare、TEST 或在子系统中查询公司文件时使用。"
---

# Alphabet NAS 数据桥接

本 Skill 是两台 Alphabet ECS 共用的 NAS 交接层。构建、部署、统一登录、权限、Manifest、Action、iframe Bridge 和 OSS 必须同时使用 `$zhuojian-subsystem-builder`；本 Skill 只说明 NAS 的真实入口、已验证共享、只读边界和验收方法。

本 Skill 由 `ZhuoJian-AI/zhuojian-enterprise-skills` 的稳定 Release 托管。每次任务先让总 Skill 更新自身和本机交接 Skills；本 Skill 被安装或更新后，立即重新读取本文件和 [当前环境](references/environment.md)。

## 定位

- NAS 是企业已有资料源，不是子系统上传盘。用户新上传的图片、视频、音频、文档和附件继续走 Runtime 的 OSS 签名上传。
- NAS 仅用于浏览、检索、下载或聚合已有共享资料。不要把 NAS 路径写进前端，也不要让浏览器、SaaS 或公网直接连接 SMB。
- 两台 ECS 都由 NAS 主动建立反向 SSH 隧道；ECS 不需要拥有 Alphabet 整个内网的路由。
- 现用 NAS 身份在部分共享具有写权限，因此“只读”目前是应用和操作边界，不是 NAS 账号的强制权限。没有新的明确授权，不得创建、覆盖、移动、重命名或删除 NAS 文件。

## 工作流程

1. 用 `$zhuojian-subsystem-builder` 登录目标 ECS，运行 Runtime 健康检查，并确定 Runtime ID。
2. 读取 [当前环境](references/environment.md)，选择与 Runtime 对应的宿主机入口、Docker 私网入口和 root-only 凭证文件。不得打印凭证内容。
3. 先确认宿主机 `127.0.0.1:10445` 监听，再用 `smbclient` 和 root-only 凭证执行共享列表查询。该检查不得上传或创建测试文件。
4. Docker 应用需要 NAS 时，接入目标 ECS 已有的 `zhuojian-nas-readonly` 内部网络，使用环境文档中的 Docker 私网入口。容器内的 `127.0.0.1` 不是 ECS 宿主机。
5. 只把业务明确需要的共享和目录开放给子系统接口。后端负责路径白名单、角色数据范围、下载审计和响应限额；前端只调用子系统的授权 API/Action。
6. 文件查询结果可以写入子系统自有数据库作为有界元数据索引，但 NAS 文件正文不复制到 ECS 或 OSS，临时预览缓存也不例外。浏览、预览和下载走有界内存流，禁用代理临时落盘。新建共享盘页面不提供上传或写回；其他系统已有附件上传规则不变。
7. 在最终应用容器中完成真实列目录或读取验收，再通过总 Skill 完成 SaaS 登记与员工端端到端测试。

## 访问边界

Alphabet 负责人明确要求原件始终留在公司 NAS；此约束不因云端有空闲硬盘或已启用 OSS 而改变。按总 Skill 的外部资料源只读规范验收。技术账号能读 `AI` 共享中的部门目录不代表普通员工都能读：SaaS 共享区授权与 NAS ACL 必须同时成立，未明确目录归属时不猜测部门范围或自动授权。

当前经现有身份验证可列出的共享为 `000`、`AI`、`outshare`、`TEST`。`商品部`、`财务部` 当前不可读；不得绕过 NAS ACL。若业务需要其他共享，由管理员先在 NAS 上授权或提供专用只读身份，再更新 ECS 的 root-only 凭证和本 Skill 的环境事实。

严禁把 NAS 密码放入 Git、Skill、源码、镜像、Manifest、前端、日志或回复。应用只能通过受控 Secret 获得所需连接字段；不要把 root-only 文件整体复制进项目仓库。

## 故障定位

- NAS 到 ECS SSH 不通：隧道传输层故障。
- ECS 无 `127.0.0.1:10445` 监听：NAS 隧道未运行或远端转发失败。
- 端口监听但 SMB 登录失败：检查 ECS root-only 凭证或 NAS 账号状态。
- 宿主机可列目录、容器失败：检查内部网络和 Docker 私网代理。
- 容器可读、SaaS 页面失败：检查子系统权限、Action、登记或 iframe Bridge，不要误报为 NAS 未接通。

## 完成标准

逐项报告，不把不同层级合并成一句“NAS 已接通”：

```text
tunnel_transport_pass  NAS 到目标 ECS 的受限反向隧道在线
host_smb_auth_pass     ECS 宿主机使用现有凭证列出允许共享
host_read_pass         ECS 对允许共享完成无写入的真实目录或文件读取
container_read_pass    最终应用容器通过内部网络完成同一读取
subsystem_contract_pass 子系统权限、Action、审计与 OSS 上传边界通过
saas_embed_e2e_pass    真实员工从 SaaS 打开页面并看到获权 NAS 资料
```

前 3 项表示 NAS 数据入口可用；只有与具体子系统有关的后 3 项也通过，才可声称该子系统已完整接入 NAS 并嵌入 SaaS。
