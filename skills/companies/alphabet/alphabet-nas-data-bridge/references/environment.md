# 当前环境

## 2026-09-29 杭州接管与 NAS 直连

真实 `enterpriseKey=aifabei`、组织 ID `65130a23-b05e-4026-9615-761ab2d4193c` 和 Runtime ID 均保持不变。生产/文化 `aifabei-hk-01` 位于杭州 `47.97.90.161`；商品动销 `aifabei-hk-48` 位于杭州 `101.37.173.94`。NAS 两条受限 SSH 隧道已直接连接这两台主机的 `22` 端口，用户仍为 `zjnas-tunnel`，宿主机回环入口均为 `127.0.0.1:10445`。

NAS 开机脚本只修改两处目标 IP；原用户、转发参数、自动重连和密钥文件路径不变。杭州主机 key 已加入受控 `known_hosts` 并使用严格校验，旧条目保留回退。密钥路径 `/var/services/homes/mawen/.ssh/zhuojian_nas_8_218_208_205`、`/var/services/homes/mawen/.ssh/zhuojian_nas_47_243_48_78` 中的旧 IP 只是文件名，不能据此删除或重建密钥。随包脚本与实际开机脚本的两处目标一致。NAS 原文件正文不参加主机或 OSS 复制，云端不缓存正文。

2026-09-29 13:14:49 CST，两台杭州主机经新直连隧道以原身份列出 `000`、`AI`、`outshare`、`TEST`；`商品部`、`财务部` 仍拒绝。生产最终 NAS 业务容器四共享有界读取通过并保持 healthy。goods 的 `172.30.33.1:445` 私网代理和 internal 网络已恢复，但本轮没有为商品业务容器增加 NAS 网络或新功能。13:32:21 CST 两条迁移临时桥的 unit、专用 key / known_hosts 及源端对应公钥、迁移 sshd 配置已精确撤除；原 LAN/NAS keys 和旧资源未动，临时源账号保留 locked/nologin 且无公钥。未开放公网 445/11433/18849。

## 当前内网隧道拓扑

```text
Alphabet 群晖 NAS 10.0.0.33:445
        │ NAS 主动建立两条受限反向 SSH 隧道
        ├──────────────► 杭州 47.97.90.161  127.0.0.1:10445
        │                    │ 私网代理
        │                    ▼
        │                 172.29.33.1:445
        │
        └──────────────► 杭州 101.37.173.94 127.0.0.1:10445
                             │ 私网代理
                             ▼
                          172.30.33.1:445
```

两台 ECS 上的内部 Docker 网络都叫 `zhuojian-nas-readonly`，但它们属于不同 Docker 主机，网段不同。SMB 没有发布到公网。

## 当前内网隧道对照

| Runtime ID | 公网管理地址 | 宿主机 SMB 入口 | Docker 私网入口 |
| --- | --- | --- | --- |
| `aifabei-hk-01` | `47.97.90.161` | `127.0.0.1:10445` | `172.29.33.1:445` |
| `aifabei-hk-48` | `101.37.173.94` | `127.0.0.1:10445` | `172.30.33.1:445` |

## 持久配置位置

- NAS 开机脚本：`/usr/local/etc/rc.d/zhuojian-nas-tunnels.sh`
- NAS 隧道私钥：NAS 用户家目录的 `.ssh/zhuojian_nas_*`；不得输出或复制。
- ECS 隧道用户：`zjnas-tunnel`；公钥被限制为只能监听本机 `127.0.0.1:10445`。
- ECS SMB 凭证：`/etc/zhuojian/integrations/alphabet-nas-readonly.smbcredentials`，必须为 root-only。
- ECS 连接元数据：`/etc/zhuojian/integrations/alphabet-nas-readonly.env`，必须为 root-only。
- ECS Docker 私网代理：`zhuojian-nas-smb-proxy.service`。

## 已验证范围

- NAS 设备：Synology DSM，SMB `445` 与 SSH `22` 在 Alphabet 内网可达。
- 共享可列目录：`000`、`AI`、`outshare`、`TEST`。
- 当前不可读：`商品部`、`财务部`。
- 当前 NAS 容量使用率约为 `93%`；不要为验证创建大文件，也不要把 OSS 内容同步回 NAS。
- 当前凭证对应的 NAS 身份在部分可读共享上同时具有写权限。默认只允许读取；强制只读需要管理员另建只读 NAS 身份后替换 ECS 凭证。

以上是交接时验证结果。每次实际开发仍要实时检查隧道、SMB 认证、目标共享 ACL 和容量，不可只引用历史状态。
