# 企业原系统人员同步

SaaS 提供统一人员接口并维护原员工、部门、角色与身份关联；企业服务器通过已有 Runtime 的企业绑定和机器凭据投递变化。AI 按本参考完成原系统适配、安装和验证，之后由服务器程序自动运行，业务负责人不必持续调用 AI。Skill 本身不是定时任务，也不代表 SaaS 已发布此能力。

已有同步正常时沿用原通道。仅有缺口时补本地采集与投递，不新增 Runtime 实例、人员库、权限系统或模型循环。不同 ERP/通讯录的字段差异留在所属企业的采集程序，不进 SaaS 公共代码或核心 Skill；企业事实保存在匹配的交接资料。

## 可用能力和授权

检查当前 SaaS 的 `features.personnelSync`：`supported:true`、`version:1`，认证声明为 `runtime-with-explicit-directory-source-grant`。已安装此版本 Skill 不等于线上支持；旧 Runtime 投影未知时可核对原始平台能力响应，不自行伪造支持标记。

企业管理员插件复用现有本人登录和管理操作通道，提供以下操作；企业 ID 由平台绑定，不让业务负责人准备管理员 Token：

| 操作键 | 用途 |
| --- | --- |
| `enterprise_directory.sources.get` | 查询已有来源，避免重复登记 |
| `enterprise_directory.create_source.post` | 授权指定原 Runtime 和来源 |
| `enterprise_directory.source_state.patch` | 按配置版本启停同步来源 |
| `enterprise_directory.binding.post` | 可信关联已有员工/部门，保留原 UUID |
| `enterprise_directory.application_binding.post` | 可选关联员工用途的原应用账号 |

HTTP 对应 `GET/POST /api/v1/organizations/{org_id}/directory-sources`、`PATCH .../{source_id}`、`POST .../{source_id}/bindings` 和 `POST .../{source_id}/application-bindings`。管理员沿用当前管理授权和确认机制；Runtime 不能给自己授予人员写权限，普通应用 `zjss_` 凭据不能投递。

创建来源指定 `runtime_id`、稳定 `source_key`、`kind:generic`，以及是否授予 `manage_employment`。钉钉来源用 `kind:dingtalk`，`corp_id` 必须匹配本企业原有配置。`manage_employment:false` 只同步资料/部门，员工 `is_active` 必须为 `null`；跟随源启停须明确授权 `true`。暂停来源只阻止继续投递，不批量停用员工。

既有稳定来源 ID 映射可复用，钉钉已登记人员/部门绑定自动复用。姓名、邮箱相同不能证明同一人。需要人工确认的绑定由 AI 展示具体原记录与 SaaS 对象再沿用管理员通道；绑定携带来源当前 `expected_version`，员工还带现有 `employee_version`。每个员工/部门只由一个人员来源维护，不另建重复账号来绕过关联冲突。

## 企业服务器上的最小适配

原系统采集程序只读当前获权数据，输出以下 JSON；已有合适的投递程序也可直接调用统一接口，无需安装随包工具。

```json
{
  "departments": [{"external_id":"original-dept-id","name":"销售部","parent_external_id":null}],
  "employees": [{"external_id":"original-user-id","display_name":"人员称呼","department_external_id":"original-dept-id","is_active":true}]
}
```

使用原系统稳定人员/部门 ID，账号名或姓名不作 ID。`is_active:false` 只来自业务已确认的明确禁用、归档或离职状态；读取失败、目录少人、钉钉账号未激活都不能推断离职。明确离职事件需校验企业、稳定 ID、时间与顺序，持久化后才确认接收；原系统的事件订阅和实际送达另验。

可复用随包 `assets/admin-runtime/personnel-sync/directory_sync.py`，Python3 标准库即可运行。按原服务器发布方式放至 `/opt/zhuojian/enterprise-directory/`，不开放入站端口。root-only 配置 `/etc/zhuojian/directory-sync.json`：

```json
{
  "source_key":"erp-staff",
  "collector_argv":["/usr/local/sbin/existing-authorized-personnel-reader"],
  "state_file":"/var/lib/zhuojian/directory/erp-staff.sqlite"
}
```

默认复用 `/etc/zhuojian/runtime.json` 和 `/etc/zhuojian/runtime-registration.key`；原部署路径不同时以 `runtime_profile`、`credential_file` 配置，不复制或在聊天显示凭据。采集命令为参数数组，不拼 shell。需要跨原系统主机读取时复用现有获权接口/SSH/只读桥接，不对公网开放数据库。

`python3 directory_sync.py --config /etc/zhuojian/directory-sync.json --preview` 只读采集并显示数量，不向 SaaS 写入或推进发送端版本。正常执行才投递。按目标授权安装随包 oneshot service/timer（默认五分钟）；AI 完成配置、服务和实际回执核对，不让负责人拷命令。SQLite 仅保存来源版本与未确认批次，不作为另一份员工权限库。

机器投递为 `POST /api/v1/ecs-publisher/directory/{source_key}/batches`，正文包含 UUID `request_id`、`dry_run`、部门和员工数组（分别最多500条），每条增加单调递增的 `source_version`。发送端持久化版本和待发批次后投递，重试保持 request_id；来源数据暂不可读也先补传已保存批次。收到相同来源/请求的真实回执才删除待办。超时结果未知不重新开户，先重试原批次或 `GET .../batches/{request_id}` 查询。

服务端 `dry_run:true` 在事务里验证后回滚，与本地 `--preview` 不同。相同请求不同内容、同版本改内容、同名未可信关联等返回409；一个批次中任一关联错误整批回滚。旧版本忽略，来源缺少某人不删除或停用该人。

## 新增、调部门、停用和现有账号

新增稳定 ID 创建原 SaaS 的普通员工和身份关联，不设置密码或自动授予业务角色；同步名册不等于打通原系统 SSO。调部门沿用同一 User UUID 和现有部门授权生命周期。明确停用走原 User 状态、会话失效及授权规则，不复制密码/角色；来源只可恢复自己停用且未被人工覆盖的人员，管理员停用优先。管理员不可直接启用来源仍明确停用的员工，避免两边反复覆盖。

SaaS 手工添加员工、建部门、分配角色继续可用；未绑定来源的手工对象不受原目录缺失影响。单向同步不把 SaaS 手工新增写回原系统。原账号后来绑定时保留原 UUID、角色、历史归属；源状态不是额外一套业务权限。

原应用登录/外部客户接入仍见 [应用用户](application-users.md)。仅对明确的员工用途账号，可将可信员工关联和 `application_binding` 接通到原应用 session-check，使该账号跟随员工生命周期；不能据此把客户导成员工、改业务角色或把应用令牌升级成员工令牌。历史入口未实际复验会话时不能称统一启停已接通。

交付分别记录 SaaS 线上能力、来源授权、采集只读结果、真实批次回执、自动触发及员工会话变化。用隔离数据验证新增/调部门/启停、重复和未知结果恢复、越企业拒绝、人工用户保留；只读人数一致不能证明自动同步或离职事件已完成。现有业务子系统不因发布本参考而重发。
