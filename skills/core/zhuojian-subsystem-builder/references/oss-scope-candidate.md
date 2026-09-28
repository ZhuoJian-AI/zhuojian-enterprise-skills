# 离线候选机 OSS 换域入口

`assets/admin-runtime/host/migrate_oss_scope.py` 与 `runtime_admin.py` 同目录，Host 安装器将其放在 `/usr/local/lib/zhuojian/`。它只支持恢复后的隔离候选主机、已有 OSS release、未启用版本的源/目标 Bucket、`apps/` 根前缀。它不创建 Bucket、不复制对象、不连接源机、不改 IP/DNS、不启动业务；普通 `configure-oss-gateway` 护栏保留。

## 输入来源

管理员先按 [跨地域迁移](region-migration.md) 冻结源写入并完成最终全量/增量校验，再生成 root-only `0600` 清单。必须真正穷尽源和目标的所有分页，不能用控制台容量、首屏/抽样结果或手工填 `true` 充当证明。`objects` 为双方完整对象集合按相同键合并，目标额外对象也不能漏掉。摘要取真实 HEAD/下载校验；`metadata` 包含 Content-Type、Content-Disposition、Content-Encoding、Content-Language、Cache-Control、Expires 以及业务使用的 `x-oss-meta-*`，去除 request-id/Last-Modified 等每次复制会变化的传输字段。空值的表达须在两边一致。

```json
{
  "schemaVersion": 1,
  "operationId": "0123456789abcdef0123456789abcdef",
  "capturedAt": "2026-09-28T00:00:00Z",
  "sourceWritesFrozen": true,
  "source": {
    "host": "<源公网地址>", "machineId": "<源 /etc/machine-id 的32位hex>",
    "runtimeSha256": "<源 runtime.json 原始字节的64位SHA256>",
    "bucket": "<源bucket>", "region": "cn-hongkong", "versioning": "Disabled",
    "enumerationComplete": true, "objectCount": 1, "totalBytes": 3
  },
  "target": {
    "host": "<目标公网地址>", "machineId": "<目标 /etc/machine-id 的32位hex>",
    "bucket": "<目标bucket>", "region": "cn-hangzhou", "versioning": "Disabled",
    "enumerationComplete": true, "objectCount": 1, "totalBytes": 3
  },
  "identity": {"enterpriseKey": "<真实企业键>", "organizationId": "<真实组织ID>", "runtimeId": "<原Runtime ID>"},
  "releaseSha256": {"<每个受管applicationSlug>": "<对应release.json原始字节SHA256>"},
  "stoppedUnits": ["nginx.service", "cron.service", "zhuojian-backup.timer", "zhuojian-backup.service"],
  "objectCount": 1, "totalBytes": 3,
  "objects": [{
    "key": "apps/<applicationSlug>/<storageKey>", "size": 3,
    "source": {"size": 3, "etag": "<ETag>", "crc64": "<十进制CRC64字符串>", "metadata": {"content-type": "text/plain"}},
    "target": {"size": 3, "etag": "<ETag>", "crc64": "<相同CRC64>", "metadata": {"content-type": "text/plain"}}
  }]
}
```

对象内容必须 CRC64 一致，或两边均提供相同 `sha256`（64位小写hex）；只有 ETag 不够。清单必须在冻结后产生且执行时不超过两小时。全部受管 release 都要列出，既有转换/凭证轮换未收尾时拒绝。源 Runtime 管理地址、身份与原始字节摘要必须匹配；目标本机 machine-id 必须匹配目标，且源/目标 host 和 machine-id 均不同。公网 IP 与 machine-id 的对应关系由管理员从本次云实例和 SSH 会话核对；文件本身不是云账号身份签名。

目标先停所有业务容器，只允许 `zhuojian-storage-gateway` 运行；上述 unit 和实际额外同步/Runtime 服务必须已停止。Runtime 可能仅为 CLI，没有常驻 daemon，脚本持有与普通发布相同的 Runtime 锁；有 daemon 的主机须将其实际 unit 加入清单并停止。网关不得发布宿主机端口。候选秘密文件仅写目标 Bucket/Endpoint 与已限定目标资源的访问凭证，必须 root-only，不进入命令参数、清单或 Git。

```sh
python3 /usr/local/lib/zhuojian/migrate_oss_scope.py \
  --manifest /root/oss-final-inventory.json \
  --candidate-env /root/oss-candidate.env
```

脚本备份 Runtime、旧网关配置、SQLite 身份库及各应用存储身份，锁定原网关镜像 ID 重建，恢复应用私网连接并执行真实隔离/CRUD 探针，最后原子更新 Runtime 的 bucket/region。应用 ID、存储令牌、release 与 source 管理地址不变；管理 IP 随后由实际受控主机接管步骤更新。`committed` 只表示该候选的存储配置已切换，不代表已开放业务或全部迁移成功。

## 中断与回退

事务在 `/srv/zhuojian/backups/oss-scope/<operationId>/journal.json` 记录状态，文件均 root-only。同一清单重跑：已提交且配置未漂移则幂等返回；未提交的持久事务先恢复旧配置/身份库并返回 `rolled-back`。准备阶段在 journal 写入前中断则拒绝重用目录，管理员检查备份后用新的最终清单/operationId继续，不能删除备份伪装重试。

目标尚未开放业务写入时可显式恢复同一事务：

```sh
python3 /usr/local/lib/zhuojian/migrate_oss_scope.py \
  --manifest /root/oss-final-inventory.json --rollback
```

回退也要求本机身份和目标服务停止；任何非网关容器在清单时间之后启动过都会拒绝，避免停止新业务后直接拿旧清单回滚。目标已有新写入后须先收口并反向同步增量，不能只运行此命令而忽略目标 Bucket 数据；不要删除旧容器来规避此检查。任一步失败都保持业务关闭；重新检查 journal、Runtime、网关配置与应用身份后再恢复业务。不要把预演用清单重复用于生产接管。
