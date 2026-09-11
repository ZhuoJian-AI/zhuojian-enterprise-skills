# 当前环境

## 固定拓扑

```text
Alphabet 群晖 NAS 10.0.0.33:445
        │ NAS 主动建立两条受限反向 SSH 隧道
        ├──────────────► ECS 8.218.208.205  127.0.0.1:10445
        │                    │ 私网代理
        │                    ▼
        │                 172.29.33.1:445
        │
        └──────────────► ECS 47.243.48.78   127.0.0.1:10445
                             │ 私网代理
                             ▼
                          172.30.33.1:445
```

两台 ECS 上的内部 Docker 网络都叫 `zhuojian-nas-readonly`，但它们属于不同 Docker 主机，网段不同。SMB 没有发布到公网。

## Runtime 对照

| Runtime ID | 公网管理地址 | 宿主机 SMB 入口 | Docker 私网入口 |
| --- | --- | --- | --- |
| `aifabei-hk-01` | `8.218.208.205` | `127.0.0.1:10445` | `172.29.33.1:445` |
| `aifabei-hk-48` | `47.243.48.78` | `127.0.0.1:10445` | `172.30.33.1:445` |

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
