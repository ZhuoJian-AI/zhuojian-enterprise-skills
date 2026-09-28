# 当前环境

## 2026-09-28 迁移候选

两台源 Runtime 的真实 `enterpriseKey` 均为 `aifabei`，组织 ID 为 `65130a23-b05e-4026-9615-761ab2d4193c`，迁移保持不变。生产/文化 `aifabei-hk-01` 从 `8.218.208.205` 迁往杭州候选 `47.97.90.161`；商品动销 `aifabei-hk-48` 从 `47.243.48.78` 迁往候选 `101.37.173.94`。下方拓扑仍是源环境，候选不能凭 IP 或资源已购就宣称接管。

NAS 端应核验目标主机 host key、受限隧道用户与 loopback `10445` 后建立目标通道，复验目标宿主机及最终业务容器列目录/流式读取，再切业务入口。旧隧道在观察期保留；NAS 文件正文不参与主机/OSS 复制。随包隧道脚本当前仍对应源环境，未核验目标前不得直接替换为候选 IP；完成真实切换后同步脚本、环境表和发布证据。

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
