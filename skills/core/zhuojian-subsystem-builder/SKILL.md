---
name: zhuojian-subsystem-builder
description: "让 AI 用业务需求和服务器登录信息，在已接入灼见的企业 ECS 上新建、修改并部署业务子系统，自动处理统一登录、角色授权、业务操作、文件存储和公司专属交接规则。用户提到灼见 SaaS、企业子系统、ECS、数据盘、跨部门模块、OSS 迁移或 iframe 接入时使用。"
---

# 灼见企业子系统

本 Skill 是所有接入灼见 SaaS 的企业共用入口。企业、服务器、既有系统和数据通道的特殊事实必须放在中央目录登记的独立交接 Skill 中，不写入本 Skill。历史名称 `aifabei-subsystem-builder` 只作兼容迁移。

每次调用本 Skill 时，同一轮先运行一次 `python <skill>/scripts/update_skill.py`，再运行一次 `python <skill>/scripts/update_managed_skills.py installed`。前者更新本 Skill，后者更新本机已经安装的企业交接 Skills。若任一命令输出 `SKILL_UPDATED` 或 `MANAGED_SKILLS_UPDATED`，先读取对应新版的版本记录，再重新读取新版 `SKILL.md` 和本次所需参考文件后继续；其他结果直接使用本地版本，细节见 [Skill 稳定版更新](references/skill-updates.md) 和 [企业交接 Skill 自动同步](references/managed-handoff-skills.md)。

业务负责人只需提供三样东西：想做什么、谁使用，以及首次出现的新服务器的 `IP + root + 密码`。公司名称可以一并说明，但只用于核对，服务器 Runtime 档案才是企业身份的权威来源。首次凭证即代表已授权当前 Codex 环境长期登录该服务器；连接成功后建立并复用本机 SSH 访问记忆，后续禁止再次向负责人索要账号密码。不要让其准备阿里云、OSS、GitHub、模型供应商或平台令牌，也不要让其选择技术方案。

## 自动判断

- 用户明确说“初始化服务器”时，执行管理员模式。
- 其他情况均执行业务模式。
- 优先扩展服务器上的现有系统；只有确实需要独立域名、数据库、发布周期或故障隔离时才新建系统。
- 暂时只能 iframe 接入的旧系统要标记“兼容模式”，不能说成已经完成原生接入。

## 业务模式

1. 按 [服务器长期访问记忆](references/server-access-memory.md) 查找已有访问档案，再按 [ECS 首次接入](references/ecs-first-access.md) 登录。新服务器先试 SSH `22`，再试管理员配置的 `443`；连接超时不代表密码错误。
2. 运行 `zhuojian-runtime doctor`。若提示服务器尚未初始化，停止部署，只告诉用户“请企业管理员先初始化这台服务器”。读取服务器非敏感 Runtime 档案中的 `enterpriseKey` 与 `runtimeId`，连同当前主机地址交给 [企业交接 Skill 自动同步](references/managed-handoff-skills.md) 的 `resolve` 流程；用户口述的公司名称只作核对，服务器档案为准。安装或更新后，必须立即读取所有匹配的交接 `SKILL.md` 再继续。
3. 检查服务器上的现有项目。若服务器源码比本地/Git 副本更新、分叉或含未同步改动，先从服务器建立开发基线，禁止用落后副本覆盖；例外见 [ECS 直接发布](references/direct-ecs-deployment.md)。读取 `subsystem.json` 识别并保留已有 `2.4` 或 `2.5` 接入版本；未知版本停止，不能猜测或只改版本号。能扩展就扩展；新项目使用内置模板创建。细则见 [原生聚合与扩展](references/native-aggregation.md)。
4. 完成业务页面、数据库和操作能力，并按 [平台接入协议](references/platform-contract.md) 接入。通用业务助手由 SaaS 提供；页面需要 OCR、语音转写、图片判断等专业 AI 时也由 SaaS 受控执行，子系统不保存模型密钥。
5. 使用 Runtime 当前提供的文件存储；不要询问用户 Bucket、令牌或服务器目录。需求涉及上传、附件、导入导出或持久文件时，读取 [文件存储与 OSS 迁移](references/object-storage.md)，校验源码时加 `--requires-file-storage`；只有 Runtime 已启用 OSS 时再加 `--requires-object-storage`。
6. 完成测试、部署和平台登记。Runtime 自动处理域名、目录和平台接入信息，AI 不读取、不复制、不展示这些秘密。
7. Runtime 校验通过后自动登记并生效，不等待管理员逐版本审核。新系统先只自动授权“系统研发者”；其他员工仍按企业管理员已绑定的业务角色访问，既有角色只在原权限上限内继承新增能力，管理员停用始终优先。

常用入口如下，参数以 `--help` 为准：

```text
zhuojian-runtime doctor
zhuojian-runtime preflight <applicationSlug>
zhuojian-runtime ensure-app <applicationSlug>
python <skill>/scripts/validate_source.py --path <项目目录>
zhuojian-runtime deploy <applicationSlug> --issue-certificate
python <skill>/scripts/publish_subsystem.py --help
python <skill>/scripts/validate_endpoint.py --help
python <skill>/scripts/e2e_acceptance.py --help
```

## 必须实现的结果

涉及角色、公共内容或个人记录时，读取 [操作权限与记录归属](references/action-permission-scopes.md)。可打开页面、可执行操作、可处理的记录分别校验；不能以角色不是全企业范围为由拒绝整页。新建及本次新增 Action 必须声明并实际实现 `permissionPolicy`；既有 2.4/2.5 缺失策略仍兼容，但必须输出待升级清单，不自动放宽。

涉及模块拆分、导航、模块导航主题或既有系统升级时，读取 [模块导航与安全迁移](references/module-navigation-migration.md)，按服务器当前契约生成新旧映射和权限影响。SaaS 提供系统导航、桌面横向模块导航及手机自动换行模块网格；手机不能要求左右滑动才能看全八个模块。嵌入页面隐藏重复导航，保留紧凑业务内容。每个子系统发布前必须登记与自身页面配色一致、通过对比度校验的 `presentation.moduleNavigationTheme`；缺失或无效时 Skill 的源码、端点及登记前校验必须失败，不得报告“已同步”。只登记受控颜色，不开放 CSS；已上线旧版本仍由 SaaS 安全回退默认色，不因 Skill 更新停用。Skill 自动更新只更新开发规范，不代表业务系统已经适配、部署或同步。

涉及页面按钮跨模块/页面跳转时，同时读取 [标准导航 Bridge](references/navigation-bridge.md)。使用平台声明的可选能力和模板封装，不拼接 SaaS 内部路由、不访问父页面 DOM，不要求业务负责人取得 SaaS 服务器权限。隐藏外壳不能替代导航接口；独立入口仍需重新鉴权。

- 员工从灼见 SaaS 登录，系统自己不再创建一套员工账号和角色。
- SaaS 组织结构只使用“企业 → 部门 → 用户”。企业公共及员工所属部门工作空间默认查看／下载，角色追加跨部门访问和写入；子系统页面、Action 与 AI 能力仍由有效角色授权，不因部门归属自动开放。实际访问以 SaaS 服务端有效权限为准；详见 [工作空间与业务授权边界](references/workspace-access.md)。不要创建 Team，也不要把子系统待办变成 SaaS 的跨部门待办。
- 企业管理员只需绑定“系统研发者”或配置业务角色；Runtime 更新不需要重复审核。多角色可以取并集，但每个页面和操作的数据范围必须单独计算，不能互相借权限。
- 页面按钮和 SaaS AI 调用同一套业务服务；修改、删除等高风险操作必须经过版本校验、确认和防重复执行。
- 系统文件统一经过模板存储层，当前可先用磁盘，以后可以按清单迁移 OSS。
- 基于业务数据生成文件时，必须走“子系统结构化数据 → SaaS 文件执行器 → 当前员工工作空间”链路；出现可预览、可下载的工作空间文件卡片后才算完成。
- 每个 AI 页面声明用途、核心实体、可回答问题、关联页面和 Action 语义；同一 SaaS 主脑结合本轮上下文理解自然表达并按需发现工具，分类仅作检索提示，不作执行门禁。子系统不另建用户会话或处理模型路由。
- OCR、语音转写、图片比较/分类、结构化抽取和业务预测等专业 AI 必须通过 SaaS 受控能力返回可校正草稿；人工确认后才调用普通 Action 写入业务记录，子系统不保存或直连模型供应商密钥。
- 所有员工页面必须同时兼容电脑、平板和手机；导航及主要操作不得被裁切，只有表格、画布等必要内容可以在自身容器内横向滚动。
- 手机适配必须用真实业务页面验证：至少在 Chromium、WebKit 的 320/390px 竖屏、844×390 横屏及桌面尺寸检查嵌入和独立入口，包括有数据的表格、模块内页面、弹窗、输入及返回。分别记录源码基线、页面覆盖、结果和未测项；静态检查通过、空白 iframe 样例或 `responsive_acceptance_pass: null` 都不算通过。浏览器模拟不能宣称苹果、华为、小米等真机已验收。局部滚动容器的网格父项也须允许收缩，不能用整页 `overflow:hidden` 掩盖裁切；窄屏不能直接隐藏关键业务指标。
- 新系统使用契约 `2.5`；已有 `2.4/2.5` 系统的普通维护保持原版本。`2.4 → 2.5` 只在用户明确要求迁移时执行。登录、权限和平台接入的技术细节由模板、Runtime 与 [平台接入协议](references/platform-contract.md) 自动落实，不转嫁给业务用户。

## 管理员模式

管理员只需为每台 ECS 初始化一次。按 [管理员与服务器初始化](references/admin-bootstrap.md) 完成 Runtime、Docker、域名、数据目录、监控、备份和平台登记；发现未初始化数据盘、磁盘告警或需要调整宿主机容量布局时，必须再按 [ECS 数据盘与容量迁移](references/data-disk-capacity.md) 执行只读盘点、授权确认、精确迁移和持久化验证；网络问题按 [SSH、VPN 与代理访问](references/ssh-access.md) 排查。初始化不能以 Runtime 健康为结束：必须继续执行 [企业交接 Skill 自动同步](references/managed-handoff-skills.md) 的“初始化后的强制收尾”，检查既有系统、数据通道和服务器特例。有特殊事实时自动创建或更新独立交接 Skill，以 `enterpriseKey + runtimeId` 为主、当前公网地址为兜底登记到唯一企业 Skills 总仓库，完成 PR、稳定 Release 和无缓存解析验证；没有特殊事实时不创建空壳 Skill，并明确报告“不需要专属交接 Skill”。管理员明确要求初始化该 ECS，即授权完成这项不含秘密的配套登记，不再另问“是否登记”。发布未成功时不得把初始化任务报告为全部完成。

完成后只向负责人提供本 Skill，以及首次连接所需的服务器 `IP + root + 密码`。业务 AI 会自动取得匹配的交接 Skill，负责人不需要 GitHub 账号或单独安装包。以后管理员只需按人员职责绑定“系统研发者”或业务角色，必要时可停用系统或 Action。

OSS 不是前置条件。未配置时使用磁盘；以后由管理员按 [文件存储与 OSS 迁移](references/object-storage.md) 迁移，不在普通发布过程中暗中切换。挂载数据盘只是本地容量放置，不等于已迁移 OSS，也不得据此改变文件存储契约。

## 交付回复

只说明系统入口、做成的功能、使用角色、自动发布状态、健康状态和文件存储状态；若员工尚无业务角色要明确说明。不要展示服务器路径、Bucket、对象前缀或任何凭证。
