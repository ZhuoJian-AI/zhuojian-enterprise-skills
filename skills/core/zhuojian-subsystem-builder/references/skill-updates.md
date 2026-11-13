# Skill 稳定版更新

`skillVersion` 是这份 Codex Skill 自身的发布版本；`contractRevision` 是业务系统与 SaaS 的接入契约。两者互不替代，Skill 更新不得改写任何项目的 `subsystem.json`。

每次调用 Skill 时，同一轮先运行一次总 Skill 更新，再更新本机已有交接 Skill：

```text
python <skill>/scripts/update_skill.py
python <skill>/scripts/update_managed_skills.py --skills-dir <当前Skill的父目录> installed
```

路径由 AI 按当前宿主自动定位，特别是 WorkBuddy 不默认使用 Codex 安装目录。

- `SKILL_UPDATE_CURRENT`：直接继续。
- `SKILL_UPDATED`：先读取新版 `skill-version.json`，再读取 `CHANGELOG.md` 中与该 `skillVersion` 对应的版本记录，最后重新读取新版 `SKILL.md` 和本次需要的参考文件后继续，不能混用新旧指令。
- `SKILL_UPDATE_MAJOR_AVAILABLE`：跨主版本不自动安装，只提醒管理员。
- `SKILL_UPDATE_WARNING`：网络或校验失败；现有本地版本保持不变，显示一句中文提示后继续任务。
- `MANAGED_SKILLS_UPDATED`：交接 Skill 已安装或更新；读取输出路径中的版本记录与新版 `SKILL.md` 后继续。
- `MANAGED_SKILLS_CURRENT`：交接 Skill 已是最新版，或当前没有匹配项。
- `MANAGED_SKILLS_MAJOR_AVAILABLE`：交接 Skill 存在跨主版本，只报告管理员，不自动替换。
- `MANAGED_SKILLS_WARNING`：目录、下载或校验失败；已有旧版保持不变。首次安装失败时不得猜测服务器特有规则。

旧独立仓库最后发布 `aifabei-subsystem-builder 1.1.0`，把已有 `1.x` 副本接到公共仓库。公共仓库随后提供同名 `1.2.0` 兼容入口，自动安装正式的 `zhuojian-subsystem-builder`。现行总 Skill 和交接 Skill 从灼见同域 /enterprise-plugin/updates/latest.json 的稳定目录取包；保留仓库身份和 SHA256 校验，不从 main 安装。GitHub 仅保存源码，旧 GitHub Release 地址只作历史兼容，不再向其上传制品。

更新器验证仓库身份、Skill 身份、稳定 SemVer、SHA-256、压缩路径、必要文件，以及压缩包内是否存在与 `skillVersion` 完全匹配的有效更新记录；任一校验失败都不安装。在同一磁盘的临时目录准备完成后才替换，替换失败会恢复旧目录。检测到 `.git` 开发工作树时不自动覆盖，开发者仍使用 Git 更新。

现行更新仅访问灼见公司 HTTPS 分发入口，员工不需要 GitHub 账号或访问 GitHub 下载。旧副本没有更新器时，需要按仓库 README 手工执行一次引导安装。正式总 Skill 在 `1.x` 内自动更新；`2.x` 等跨主版本由管理员明确升级。

新系统始终生成 `contractRevision=2.5`。维护已有系统时先读取 `subsystem.json`，只接受当前 Skill 明确支持的版本并保持原值。`2.4 → 2.5` 是独立迁移任务，必须由用户明确要求，并同时迁移凭证、SSO、Runtime 配置和端点验收，禁止只改版本号。

维护者发布稳定版时，必须先更新对应 Skill 的 `skill-version.json`，并在其 `CHANGELOG.md` 增加同版本章节；测试通过并合并到总仓库 `main` 后，才能从该合并提交在公司 CI 构建独立 Skill 压缩包和稳定 catalog.json，再沿已登记的公司分发入口发布。构建器使用 --download-base-url 指向该次不可变版本目录，latest.json 最后切换；保留旧制品、哈希及回退。只更新 `main` 不会让用户自动更新。
