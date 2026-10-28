# 企业代码、数据的机外备份与恢复

完整范围与证据按 [备份覆盖与恢复验收](recovery-acceptance.md) 核对。旧 Runtime `backup` / `backup-all` 可能切维护页并停止容器；保持线上使用时先检查本机入口实现，改用已验收的在线一致性工具。在线恢复包保留真实方法标志，不冒充旧停写 schema；上传器、机外导出和隔离恢复必须同时识别其实际数据库目标及 OSS 附件清单。

企业负责人只确认业务范围，获授权 Codex 可以用企业 root 完成以下操作。服务器上的 Git 是日常版本记录；同服务器上的 Git 和备份会随整机故障一起丢失，因此不能把它们称为机外备份。无需强制购买 GitHub、逐系统申请云权限或操作前端。

## 一次性准备与企业隔离

复用同地域的**共享私有备份 Bucket**，与业务附件 Bucket 分开。每台企业服务器只拿到本企业当前环境的备份 RAM 身份：

```text
enterprises/<组织UUID>/<环境>/backups/applications/<applicationSlug>/archives/<恢复点>.tar.gz
enterprises/<组织UUID>/<环境>/backups/applications/<applicationSlug>/manifests/<恢复点>.tar.gz.json
```

组织 UUID 与环境来自 `/etc/zhuojian/runtime.json`，不从聊天、应用请求或任意参数拼接。该共享桶须启用版本控制、保持私有并阻止公共访问。企业 root 可以备份和恢复本企业各系统；不得持有能读其他企业的共享桶总密钥。含 Secret 的归档只进这个私有备份范围，使用 HTTPS 与 OSS 服务端 AES256 加密；不放入业务网关、公共下载、Git、日志或聊天。

获权管理员 AI 初始配置最小 RAM 策略，将占位值替换为真实值。以下 `<备份前缀>` 是 `enterprises/<组织UUID>/<环境>/backups`，不是可以由调用方修改的范围：

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "oss:GetBucketVersioning",
      "Resource": "acs:oss:*:*:<共享备份Bucket>"
    },
    {
      "Effect": "Allow",
      "Action": "oss:ListObjects",
      "Resource": "acs:oss:*:*:<共享备份Bucket>",
      "Condition": {"StringLike": {"oss:Prefix": ["<备份前缀>", "<备份前缀>/*"]}}
    },
    {
      "Effect": "Allow",
      "Action": ["oss:GetObject", "oss:GetObjectVersion", "oss:PutObject", "oss:PutObjectAcl", "oss:ListParts"],
      "Resource": "acs:oss:*:*:<共享备份Bucket>/<备份前缀>/*"
    }
  ]
}
```

不用 `oss:ListMultipartUploads`：官方权限表没有为它提供 `oss:Prefix` 条件，不能为恢复一个上传而允许企业列举整桶上传任务。不给企业备份身份删除云端对象、删除历史版本、改桶 ACL/策略/生命周期的权限。按既定保留期清理云端历史版本及长时间未完成分片，由初始化时在 Bucket 上配置企业前缀 lifecycle 完成；规则必须核对真实费用和恢复保留期，CLI 不擅自设置。

凭据只写入 root:root `0600` 的 `/etc/zhuojian/backup-oss.env`，格式与既有网关一致，不通过命令参数传递：

```text
OSS_ENDPOINT=https://oss-<地域>-internal.aliyuncs.com
OSS_BUCKET=<共享备份Bucket>
OSS_ACCESS_KEY_ID=<只写入受保护文件>
OSS_ACCESS_KEY_SECRET=<只写入受保护文件>
```

企业服务器位于同地域云内时使用 HTTPS 内网 Endpoint；异地恢复机按已登记网络使用公网 Endpoint。允许 STS 时可另有 `OSS_SECURITY_TOKEN`，但定时任务需要可续期的身份机制；不能把会过期的一次性 Token 当成永久初始化。

## 安装与配置

平台已预绑定 Runtime 时，优先走 [受限身份自动领取及定时续期](runtime-storage-bootstrap.md)，无需企业负责人提供云账号或 Token。该路径接入新的在线定时链，并自动上报平台状态；下面的手工云凭据命令保留为已获权管理员的旧部署兼容入口。

更新 Skill 和 Runtime helper 后，从该 Skill 根目录执行：

```sh
python3 scripts/install_runtime_backup.py
zhuojian-backup-oss configure --bucket <共享备份Bucket> --region cn-hangzhou
zhuojian-backup-oss status
zhuojian-backup-oss probe
```

安装器只安装独立 root CLI 与官方 oss2 依赖，不创建桶、RAM、定时任务或上传数据；失败时保留原 wrapper。已存在的不明安装路径一律不覆盖。依赖获取按服务器登记的国内源或命令级网络路径执行，不修改全局代理。`configure` 读取受保护身份文件、验证企业外列举/读/写/删拒绝与版本控制，再在 Runtime 操作锁下写入独立 `backupStorage`；已有不同配置拒绝隐式切换。`status` 只反映配置，`probe` 只证明边界和版本控制，二者均不代表备份已上传或可恢复。

首次云权限初始化由已获权管理员 AI 完成；之后企业 Codex 不需要平台管理员为每个系统开通。若当前还没有 `backupStorage` 或云凭据，明确报告“机外备份未配置”，保留本地恢复点，不假报已上 OSS。

## 生成、上传与核验

```sh
zhuojian-runtime backup <applicationSlug>
zhuojian-backup-oss publish <applicationSlug> --archive /srv/zhuojian/backups/<applicationSlug>/<恢复点>.tar.gz
zhuojian-backup-oss list <applicationSlug>
zhuojian-backup-oss verify <applicationSlug> --archive-name <恢复点>.tar.gz
```

上传器接受 Runtime schemaVersion=2 的受控停写一致性归档，或 schemaVersion=3 的真实在线 SQLite/文件/对象快照。两者均要求字节数、SHA-256、内嵌 `code/repository.bundle` 的哈希和实际恢复校验、仓库 HEAD 与运行 release commit；在线快照另核 manifest、数据库完整性和文件引用。不能把在线包伪装为停写包。旧 schema1 的数据归档仍可按旧 Runtime 路径恢复，但不能被包装成包含 Git 的完整机外恢复点。

归档以有界分片上传，超过业务网关的 512 MiB 上限也可处理，不把整包读入内存。持久化 upload journal，并对同一恢复点加进程锁。有 uploadId 的中断重传同编号分片；完成请求超时先 HEAD/GET 核对，必要时只续原上传。初始化请求超时且 uploadId 未保存时，不盲目重提、也不扩大权限列举全桶；保留该恢复点及 journal，生成一个新 Runtime 恢复点继续上传，旧分片由既有 lifecycle 回收。

只有拿到非空 `versionId`、完整 GET 该精确版本并验证 SHA-256/字节数、确认对象当前版本及指定版本均拒绝匿名读取后才写远端 manifest 和本地 `.remote.json`，并标为 `offServer=true`。重复执行会核对既有 manifest 与精确对象版本，不覆盖内容冲突。未知写结果必须先读回；不要通过删 journal 来“修复”。版本控制开启时 `x-oss-forbid-overwrite` 不提供不可覆盖保证；恢复证据依靠精确版本与哈希，**不宣称 WORM 防篡改**。

## 下一位 Codex 如何发现并恢复

```sh
zhuojian-backup-oss list <applicationSlug>
zhuojian-backup-oss stage-restore <applicationSlug> \
  --archive-name <恢复点>.tar.gz \
  --destination /srv/zhuojian/restore-checks/<唯一验收目录>
```

`list` 从企业/环境/系统的 OSS manifest 前缀发现恢复点，不依赖旧服务器还活着；恢复机先绑定同企业 Runtime 身份和本企业备份 RAM 权限。列表每项含桶、对象键、精确版本、时间、字节数、SHA 与 Git commit。旧恢复点不会因本地归档清理而丢失入口。

`stage-restore` 只接受不存在的新目录，完整下载并验哈希，拒绝穿越、符号链接和特殊设备，检查空间，再解包到独立目录并验证 Git bundle、独立 clone、HEAD 与运行 commit。它不会覆盖在用代码、数据库、Secret 或 release。输出 `gitVerified=true` 仍明确保留 `businessDatabaseVerified=false`：Codex 接下来必须用独立容器/端口验证该业务数据库一致性、关键记录和文件引用，再走项目既定维护窗口恢复/验收流程。不能把 Git 验证成功等同于业务恢复成功。

OSS 业务附件不在普通 Runtime tar 中；跨业务附件的恢复点还需独立对象版本/清单和引用一致性验证。NAS/道讯原件保留本地源时不偷偷全量复制进备份桶；需按已确定数据边界验证读取链路。

## 自动备份与有限本地清理

已配置平台存储绑定的新 Runtime 默认用 `zhuojian-storage-bootstrap` 在线链，不安装下面会继续调用旧 `backup-all` 的兼容 drop-in。已有经过验收的在线计划、源缺失集合和定时器由初始化 AI 精确保留并登记其真实 unit 名称。定时器、计划登记和凭据探针都不构成成功恢复点。

逐系统完成真实上传和隔离恢复后，AI 可把随附的 `assets/admin-runtime/backup/20-off-server.conf` 精确安装到 `/etc/systemd/system/zhuojian-backup.service.d/20-off-server.conf`，核对原 unit 仍是登记的 `zhuojian-runtime backup-all`，运行 `systemd-analyze verify` 和 `systemctl daemon-reload`。不得覆盖同目录的其他 drop-in。它在已有备份服务结束后执行 `publish-latest`，某个系统本地失败也仍检查其他成功恢复点；失败保留本地并让服务状态可见。无需再建一个抢占停机窗口的备份定时器。

`publish-latest` 仅扫描 Runtime 管理的 release，并逐应用报告成功或失败；unit 最近成功、每个系统远端 manifest 和真实恢复演练三者都要核对。设置了定时器不代表最近运行成功。

```sh
# 默认只列计划；保留数量由容量和业务恢复期决定，最低 2 个本地恢复点。
zhuojian-backup-oss prune-local <applicationSlug> --keep 7
zhuojian-backup-oss prune-local <applicationSlug> --keep 7 --apply
```

只有既有远端 manifest 与本地字节/哈希一致、且执行清理当时再次完整回读精确远端版本成功，才逐文件删除较老本地归档及其 sidecar/journal，保留 `.remote.json` 索引和最新 N 份本地归档。失败项全部保留，不递归删除目录、不删除云端对象、不清 Git 或业务文件。新工具默认不启用自动清理；初始化 AI 根据已授权保留策略接入定期执行。日常每个系统的备份体积、留存天数和失败趋势都要进入容量估算，不能保证“定期清理就不会占太多磁盘”。

依据：[官方 RAM 权限表](https://www.alibabacloud.com/help/en/ram/api-object-storage-service)、[官方 OSS 分片上传](https://www.alibabacloud.com/help/en/oss/developer-reference/use-oss-python-sdk-to-multipart-upload)、[版本控制下的上传语义](https://www.alibabacloud.com/help/en/oss/developer-reference/upload-an-object)、[官方 Python SDK](https://github.com/aliyun/aliyun-oss-python-sdk)。
