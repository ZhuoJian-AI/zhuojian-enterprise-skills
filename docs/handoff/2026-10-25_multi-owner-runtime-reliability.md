# 多负责人共享 Runtime 发布可靠性

日期：2026-10-25。分支：`codex/multi-owner-runtime-20261025`，基线 `5d6ffe63a37da49e77140f3fc4ec07b2f804696a`，任务认领提交 `74c8b9e`。本交接仅指源码和隔离验收；未 push、合并、部署或修改生产。

## 责任与实现

企业 AI 可继续共用 root，按负责人已确认的具体业务范围自主维护，没有新增人员权限体系或前端批准步骤。Runtime 负责同机并发发布、代码恢复与受管数据备份；SaaS 和主 Skill 的业务授权/对接流程由根任务另行实现。本分支未改核心版本、CHANGELOG、SKILL.md 或模板 app.py。

- 构建从完整 Git SHA 的私有临时归档读取，拒绝子模块/链接/越界项，不把共享工作树的后续编辑、`.git` 或未跟踪 Secret 加入镜像。默认发布仍要求规范目录干净；`--source-commit` 允许同仓库任务 worktree 的提交，同时保留其他任务的未提交文件。
- `preflight` 返回 `expectedCurrentCommit`；`deploy --expected-current-commit` 在 Runtime 锁内比较实际运行基线。普通发布还必须包含现运行 commit 的祖先历史，迟到任务不能覆盖已发布功能。已有脚本不传 CAS 参数仍兼容，但必须通过祖先门槛；显式 rollback 保留并支持当前版本比较。
- 构建前将运行与候选提交固定在 `refs/zhuojian/releases/<SHA>`，拒绝覆盖同名异值 ref。发布历史不再截断到 20 条，没有新增自动清理或全局 prune。
- 更新/回滚先持久记录 `releaseSwitch`，实际停机前通过 Nginx 统一返回结构化维护响应，停止原实例，创建并校验安全备份后才启动候选。候选健康后重开；失败或进程中断按持久事务恢复旧实例，先 health、再 Nginx、最后协调 SaaS 意图。
- 定时/手动备份新增 `backupMaintenance`，同样支持中断恢复。维护时间取决于数据量和启动时间，明确不是零停机；现有启动即同步/定时后台写入的应用不直接双起。
- OSS helper 支持 `--namespace-mode enterprise-v1|legacy-apps`。共享前缀从可信 profile 派生 `enterprises/<organizationId>/<environment>/apps`，probe 验证 exact rootPrefix。已有配置省略 mode 仍继承 legacy，空/新配置默认 enterprise-v1；已有 OSS release 时拒绝直接改 bucket/region/prefix。Gateway/机外上传器由存储代理交付。
- direct-ecs 文档移除每次让 SaaS 平台管理员前端实点的要求，改 Runtime 登记证据与获权员工真实业务入口验收；平台 Console 公共能力归 SaaS 回归。

## 备份格式与兼容

同一目录内精确 `.tar.gz` 与 `.tar.gz.json`，新 sidecar `schemaVersion:2`，保留旧的 managedBy/applicationSlug/createdAt/commit/archive/sha256/consistentOfflineSnapshot，新增 `sizeBytes`、`offServer:false` 和 source：

```json
{
  "bundleMember": "code/repository.bundle",
  "bundleSha256": "<sha256>",
  "headCommit": "<full-sha>",
  "requiredReleaseCommit": "<running-full-sha>",
  "workingTreeClean": true,
  "uncommittedStateIncluded": false,
  "restoreVerified": true
}
```

Git bundle 保存全部 refs、HEAD 和运行提交，执行真实 `git bundle verify`，独立 mirror clone 后验证运行提交和 HEAD 可读。归档包含 data、config/app.env、恢复用正常 release.json、原 nginx.conf 和 code/repository.bundle；读回全部归档文件后记录 SHA256/大小。未提交源码不冒称已经备份。旧 v1 归档仍可通过 restore 恢复 data；新 code 成员不会自动覆盖项目或配置。release.json 保持现有结构，仅增加可选恢复/lastDeployment 字段；无新数据库迁移。

本机备份不包含外部数据库、NAS、道讯、OSS 对象、全局 Runtime 登记凭证或 Gateway 管理状态。机外备份必须由存储上传器对精确归档及 manifest 返回对象版本、完整读回校验和远端回执；仅 `offServer:false` 不能称机外成功。上传器接口单独安装，无未知 API hook。

## 验收

Windows Python 环境运行：

```text
D:/Agent_Project/SaaS-platform/audit-2026-10-18/enterprise-notifications/skill-test-venv/Scripts/python.exe -m pytest tests/runtime_host assets/admin-runtime/host/tests -q --tb=short
```

结果：**211 passed, 1 skipped**（Windows 无 POSIX 文件权限语义）。新用例使用真实临时 Git、独立 worktree、detached commit、Git bundle clone、tar 数据恢复与持久 release 文件；Docker/Nginx/SaaS 边界使用模拟，不接生产。覆盖并发编辑、迟到提交、CAS 冲突、运行源码引用、备份失败、候选健康失败、定时备份恢复失败时保留维护、正常切换顺序，以及企业前缀不匹配。原宿主中断恢复/网络挂载/存储轮换/安装事务集合一同通过。`git diff --check` 通过。

真实 Linux 权限、Nginx 配置加载、安装后的数据库备份与员工入口仍须由根任务在交付环境验证；这里没有把模拟 Docker 测试当实际生产切换。旧应用的数据库迁移必须兼容回退，helper 不自动撤销业务数据库变更或外部副作用。

## 整合注意

1. 本分支 helper 与存储代理 Gateway 的 `probe --expected-root-prefix` 必须一起交付；旧 Gateway 没有此接口时配置过程明确失败，不静默接受旧范围。
2. 根任务在 publisher SDK 补齐 `--use-running-release` 对 canonical dirty worktree 的兼容。在此之前可传本任务干净 worktree；不得清理其他负责人的未完成修改。
3. 保持根任务负责版本、主 Skill、双账号同步和最终发布。部署 helper 本身不代表业务系统已按新流程完成一次更新/回滚。
