# 企业交接 Skill 自动同步

## 目的

`zhuojian-subsystem-builder` 是所有企业共用的 SaaS 与 ECS 契约。某家公司、某台服务器、某个既有系统或数据通道的特殊事实放在独立交接 Skill 中。业务负责人首次只接收总 Skill，并为新服务器提供一次 `IP + root + 密码`；不要求其创建 GitHub 仓库、选择交接包或维护版本。

所有稳定版由唯一公共仓库 `ZhuoJian-AI/zhuojian-enterprise-skills` 发布。一个仓库可以包含多个独立 Skill；每个 Skill 保留自己的 `skillVersion`、更新记录、压缩包和 SHA-256。

## 每轮更新

在登录任何服务器前运行：

```text
python <skill>/scripts/update_skill.py
python <skill>/scripts/update_managed_skills.py installed
```

第一条更新总 Skill；第二条只更新本机已经安装并出现在稳定目录中的交接 Skill。更新失败时保留旧版；跨主版本只报告，不自动替换。

任一命令输出更新后，立即读取输出路径中的 `skill-version.json`、对应 `CHANGELOG.md` 版本段和新版 `SKILL.md`。同一轮不得继续使用已被替换的旧指令。

## 登录后的识别

管理员初始化 ECS 时，非敏感 Runtime 档案固定记录 `enterpriseKey` 与 `runtimeId`。登录并通过 `zhuojian-runtime doctor` 后读取 `/etc/zhuojian/runtime.json`，不得输出其中的秘密引用或其他配置。然后运行：

```text
python <skill>/scripts/update_managed_skills.py resolve \
  --enterprise-key <enterpriseKey> \
  --runtime-id <runtimeId> \
  --host <本次登录地址>
```

匹配顺序是 `runtimeId`、主机地址、企业级无服务器限定规则。主机地址用于首次兜底；长期归属以 ECS 档案为准。用户顺手给出的公司名称只作一致性核对，不能覆盖服务器档案。二者不一致时停止选择交接 Skill并报告管理员。

`resolve` 会安装尚不存在的交接 Skill，也会升级同主版本的旧副本。输出 `MANAGED_SKILLS_UPDATED` 后，立即读取输出路径中的交接 `SKILL.md` 和本次任务明确要求的 references；交接 Skill 补充总契约，不能取代或放宽总契约。

目录没有匹配项时继续使用总 Skill，并明确说明“管理员尚未为这台 ECS 登记专属交接 Skill”。目录声明了匹配项但下载、校验或安装失败时，不得猜测服务器特有规则；已有旧版可以继续使用，首次安装失败则停止依赖特殊环境的操作并通知管理员。

## 初始化后的强制收尾

管理员明确要求初始化一台 ECS 后，交接审计和必要的中央登记属于同一个初始化任务，不等待管理员再次提醒或确认。Runtime、Docker、域名、存储与最小应用验收成功，不代表初始化任务已经全部完成。

先读取刚写入的 `/etc/zhuojian/runtime.json`，取得准确的 `enterpriseKey`、`runtimeId` 和当前公网地址，再只读检查该 ECS 的既有系统与集成。以下事实不能由通用 Runtime 自动推导，任一存在时都需要独立交接 Skill：

- 已经运行、即将交给业务负责人维护的既有系统及其真实源码基线；
- 专用数据库、API、网关、反向隧道、VPN、Docker 私网或固定端口；
- 外部数据只读、允许写入、同步频率、业务截止日、字段口径等边界；
- 特殊登录兼容、角色限制、存储现状、发布顺序、故障诊断或不可触碰的同机资源。

只有通用 Runtime 能完整表达的新空白 ECS 不创建空壳交接 Skill。最终回复必须明确写出“未发现需要专属交接 Skill 的特殊事实，本次无需登记”，避免管理员以后误以为漏做。

发现特殊事实时自动完成以下流程：

1. 打开或克隆唯一公共仓库 `ZhuoJian-AI/zhuojian-enterprise-skills`，先读取仓库 `AGENTS.md`、最新 `catalog.json` 和同公司的现有 Skills。已有 Skill 覆盖同一环境时原地更新并递增 SemVer，不创建同义重复项。
2. 在 `skills/companies/<enterpriseKey>/<skill-name>/` 创建公司前缀的唯一 Skill。至少包含 `SKILL.md`、`skill-version.json` 和 `CHANGELOG.md`；按需加入 `references/`、`scripts/` 与 `agents/openai.yaml`。只写入以后会改变 AI 判断的稳定事实，不复制通用搭建规则。
3. `skill-version.json` 固定声明 `managedBy: ZhuoJian-AI/zhuojian-enterprise-skills`。在 `catalog.json` 中登记准确 `enterpriseKeys`，并优先写入本次 Runtime 的 `runtimeIds`；服务器公网地址写入 `hosts` 作为首次或换机前的兜底。不得仅凭公司名称把服务器特例加载到该公司的全部 ECS。
4. 不把 ECS 密码、SSH 私钥、数据库凭证、令牌、客户数据、本机访问档案或 Secret 值放进仓库或发布包。交接 Skill 只记录凭证保存位置和复用方式；发现现有交接材料含秘密时先移除，再进入 Git 历史。
5. 使用 `codex/<description>` 分支，精确暂存本次文件，运行受影响 Skill 测试、逐 Skill 快速校验、秘密扫描和 `git diff --check`，通过 PR 合并。不得直接推送 `main`，不得把无关改动带入提交。
6. 从合并后的干净 `main` 构建下一个未占用的不可变 `bundle-v<version>`，发布每个 Skill 的独立 ZIP、SHA-256、稳定 `catalog.json` 和总 Skill 更新清单。Release 上传或校验失败时保留仓库源码，但必须报告“交接 Skill 尚未对业务负责人可用”，不能假装发布完成。
7. 使用空临时 Skills 目录分别按新 `runtimeId` 和公网地址运行 `resolve`。两种方式都必须只安装该 ECS 应取得的交接 Skills，版本与摘要和 Release 一致；验证后再同步管理员本机副本。

若管理员环境没有 GitHub 写权限，仍应在隔离分支或临时目录生成并校验不含秘密的交接 Skill 草稿，然后报告中央发布被 GitHub 写权限阻塞；不得向业务负责人索要 GitHub 账号，也不得把未发布草稿说成已经自动同步。

旧 `ZhuoJian-AI/aifabei-subsystem-builder` 仓库保留历史升级桥梁；中央目录中的同名兼容 Skill 会继续把旧用户迁移到 `zhuojian-subsystem-builder`。后续正式总 Skill 和交接 Skill 都由企业 Skills 总仓库发布。
