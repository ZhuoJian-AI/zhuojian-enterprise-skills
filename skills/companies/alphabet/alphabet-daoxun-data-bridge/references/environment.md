# 当前环境

## 固定拓扑

```text
Alphabet 内网 Windows / SQL Server
  10.0.0.181:1433
       │ 内网服务器主动建立反向 SSH 隧道
       ▼
Alphabet ECS 8.218.208.205
  127.0.0.1:11433
       │ 已启用宿主机到 Docker 私网的只读数据代理
       ▼
Docker 私网入口 172.29.181.1:11433
       ▼
道讯数据子系统 → 灼见 SaaS iframe / Action
```

ECS 不拥有到 `10.0.0.0/24` 的通用路由。直接探测 `10.0.0.181:1433` 失败不代表上述反向隧道失败。网络挂载也与 SQL Server 访问无关。

## 已完成

- 内网服务器能够访问 ECS 的 SSH 入口。
- 专用反向隧道已配置为开机启动和退出后循环重连。
- ECS 只在回环地址监听隧道入口，没有新增公网数据库端口。
- 已从 ECS 收到 SQL Server TDS PRELOGIN 响应。
- 已在内网服务器本机使用 Windows 集成认证执行过只读数据库元数据查询，确认 SQL Server 在线。
- 已在 `H_TRADE` 建立专用只读身份；它属于 `db_datareader`，不属于 `db_datawriter` 或 `db_owner`，并显式拒绝增删改和执行权限。
- 凭证保存在 ECS root-only 集成配置 `/etc/zhuojian/integrations/daoxun-readonly.env`，不得输出其密码。宿主机连接字段和 Docker 连接字段都记录在该配置中。
- 已建立内部 Docker 网络 `zhuojian-daoxun-readonly`，容器入口为 `172.29.181.1:11433`；持久代理服务已启用并处于运行状态。
- 已从 ECS 宿主机和加入该网络的临时 Docker 容器完成认证、数据库确认和真实业务表 `SELECT`；SQL Server 2008 R2 使用 TDS `7.0` 验收通过。

以上事实需要在每次实际开发时实时复核，不能只引用历史结果。

## 尚未完成

- 未基于道讯数据构建、发布或登记具体 SaaS 子系统。
- 新应用部署时仍需加入 `zhuojian-daoxun-readonly`，从 root-only 集成配置向该应用的受控 Secret 注入连接字段，并在最终镜像中复验。

## 正确诊断口径

- `127.0.0.1:11433` 无监听：隧道传输未就绪。
- TDS PRELOGIN 成功、登录失败：网络已通，检查 root-only 集成配置、TDS `7.0` 兼容设置和只读身份状态。
- ECS 登录查询成功、容器失败：宿主机已通，检查应用是否加入 `zhuojian-daoxun-readonly` 并使用 Docker 私网入口。
- 容器查询成功、SaaS 页面失败：数据库链路已通，问题位于应用契约、部署、登记或员工授权。

不要把上述不同层级统一写成“网络没通”。
