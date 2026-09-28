# 当前环境

## 2026-09-28 杭州恢复与临时中继

真实 `enterpriseKey=aifabei`、组织 ID `65130a23-b05e-4026-9615-761ab2d4193c` 和 Runtime ID 均保持不变。生产/文化 `aifabei-hk-01` 已恢复到杭州 `47.97.90.161`；商品动销 `aifabei-hk-48` 已在杭州 `101.37.173.94` 启动并健康。生产新机 `127.0.0.1:10445` 经受限 SSH 临时桥连接旧 `8.218.208.205` 的 NAS 入口，Docker 仍用 `172.29.33.1:445`，SMB 认证列表已通过。新 goods 的 NAS 访问未据本轮 goods HTTP 验收自动视为通过。

NAS 内网客户端仍连接香港，下方原始拓扑与随包隧道脚本暂时保留。企业内网维护时先核验杭州主机 host key，停对应临时桥释放 10445，再改客户端并从最终业务容器验收目录/流式读取；失败恢复旧客户端与桥。确认直连后才撤专用临时 key/单元并同步随包脚本，不删除原 NAS keys。NAS 原文件正文不参加主机或 OSS 复制，云端不缓存正文。

2026-09-29 00:02 复核：杭州生产侧已用原受控身份认证并列出 `000`、`AI`、`outshare`、`TEST`；新生产 SSH 443 同可信 host key 验证通过。未开放公网 445/11433/18849。内网客户端仍未改连杭州，这些结果不代表直连切换已经完成。

## 原内网隧道拓扑（香港落点仍在使用）

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

## 原内网隧道对照（香港仅中继）

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
