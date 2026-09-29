# 当前环境

## 2026-09-29 杭州接管与内网直连

杭州 `47.97.90.161` 已恢复源 `8.218.208.205` 的 Runtime 和数据；保留 `enterpriseKey=aifabei`、`runtimeId=aifabei-hk-01`、`organizationId=65130a23-b05e-4026-9615-761ab2d4193c` 与 `hk01.aifabei.staging.zhuojianai.com`，展示名与历史地域缩写不覆盖身份。

生产协同、企业文化、NAS 三个受管 release 保留 `oss-gateway`。Runtime 网关已通过受控 helper 切到 `alphabet-prod-hz-files-20260928` / `cn-hangzhou`：266 对象、90,128,812 bytes，大小/CRC64/内容元数据一致，7 项真实存储 probe 通过。三业务在杭州以原镜像启动，health 与 HTTPS/TLS 均通过；旧业务和网关停止，旧域名入口反代杭州保持唯一写入。总迁移任务已独立通过真实员工 SSO 打开模块验收，不能由此推定手机真机全通过。生产协同手机页面既存 overflow 本轮未修改 UI，保留后续单独修复事项。

内网 Windows 的 SYSTEM 任务 `Zhuojian-DbBridge-HTrade` 已改连 `root@47.97.90.161` 的 SSH `22`，保留原反向转发：杭州 `127.0.0.1:11433` → 内网 Windows `127.0.0.1:1433`。Docker 仍用 `172.29.181.1:11433`，没有开放公网数据库端口。原 LAN 密钥及回退资料保留，不能因密钥文件名包含旧 IP 就删除或重建。

2026-09-29 13:12:40 CST，从杭州经直连隧道完成 `H_TRADE`（SQL Server `10.50.1600.1`）真实只读认证查询及有界业务读取；`INSERT`、`UPDATE`、`DELETE` 权限均为 0。保留 TDS `7.0` 兼容要求。13:32:21 CST 原生产临时桥已停用并删除专用 unit / key / known_hosts，香港源对应公钥和迁移 sshd 配置已撤除、语法检查后 reload；原 LAN/NAS keys 未动。临时源账号保留 locked/nologin 且无公钥。不以这次数据通路检查替代任何新应用的最终镜像或 SSO 验收。

## 当前内网隧道拓扑

```text
Alphabet 内网 Windows / SQL Server
  10.0.0.181:1433
       │ 内网服务器主动建立反向 SSH 隧道
       ▼
Alphabet 杭州主机 47.97.90.161
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
