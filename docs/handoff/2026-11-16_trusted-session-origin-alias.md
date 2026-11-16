# Builder62：可信SSO来源贯通到iframe

真实Scene验收证明61只修浏览器来源仍不够：SSO已验证实际父域别名，但模板bootstrap固定返回canonical，导致postMessage目标与父域不同。61/67和静态58仅保留源码/tag/CI，未活化、未安装服务器kit或双账号、未更新文件库；不重写旧tag，不将其CI成功称为完整交付。

62在原SSO导航allowlist、Sec-Fetch-Dest、换码及claims校验全部成功后，将已验证referring_origin存入服务端会话。bootstrap先原实时身份/范围核权，再从该受控会话读取并复验HTTPS和原配置允许集合；不读取请求参数、正文、后续Origin/referrer补授权。缺绑定的旧会话及无效/已不允许的Origin返回409要求从SaaS重新打开；不猜canonical。原身份、角色、范围、账号与业务数据不清除。CSP的父域集合与既有SSO允许集合一致。

回归实际执行生成模板的SSO→会话→bootstrap，覆盖canonical与配置别名、恶意来源不换码、失败claims不保存、9类缺失/污染会话拒绝及旧会话正常新SSO恢复。另把真实生成后端/其bootstrap与实际Chrome iframe连在一起，以缺失document.referrer分别在两个合法父域的电脑/手机模拟验证真实ready、加载解除、实际列表与无横溢出；这是隔离的合成模板环境，SaaS传输模拟，不能冒称真实员工或生产数据验收。原账号真实Scene验收由拥有方单列。

保留61的当前Action初始化与可选SDK隔离：ready表示交互页面而非所有查询成功，write/upload-only不需额外query，读失败呈独立错误，刷新保留草稿。62/bundle68/static59的完整公司CI、正式分发、SaaS baked部署、默认更新器、两Windows/现役kit及客户端结果等待独立回执。

## 正式发布与安装回执（2026-11-16 UTC）

本节记录后续正式结果，保留上面的候选阶段说明。PR131 已合入 core main `3b97f9eb8cc8270edf8b51ba1668d42be93f06fe`，不可变 tag 为 `bundle-v1.4.68`；Skill 版本1.1.62、插件0.1.59、契约2.4/2.5分别维护。61/bundle67和静态58只保留候选源码/tag/CI证据，从未活化、安装 kit 或覆盖两个 Windows 账号。

- Windows完整核心测试1022 passed /86 skipped；quick_validate通过。公司候选run1794839993975100与exact-main run1794840233865116均成功，每次1043 passed /65 skipped，另maintenance24 passed。Node执行实际模板和导航SDK，覆盖两域别名、错误来源、缺失/迟到SDK、query-only、write/upload-only、无files、读失败与草稿刷新/离开。
- SaaS源码PR1227/main `be0005e6cc8d1acd123daf575517a4f93837050d` 同步独立Skill211文件及两份内嵌JSON。原Maintenance source/manifest runs1794840527749732、1794840946234183各426通过；受保护backend/worker发布已healthy，manifest main `924983df2b5529f6e48455ffe9ee260c22968569`。实际容器两JSON原始SHA与源码相同，原生成函数的211下载内容逐一相同；其余7服务ID及9服务配置哈希保持。后端发布由SaaS拥有方执行，不能只凭源码合并推断上线。
- 静态分发沿原公司CI run1794840598736875/source `be0005e6` 构建；PR1229/main `ad42d0fdb3785e5464c4dcc4206113b8fa7136f2` 登记后，原受保护入口完成stage、prepare、activate `plugin-0159-company-20261116`，镜像 `sha256:8b6a4c89d64f2e173acf9554665270ad6f2b47ed84dd8119761c42e62dcbce06`。1655公开对象保留全部旧对象，36个变更文件独立HTTPS200/SHA匹配；原Skill60不可变URL仍200且SHA不变。
- 原企业文件库同一个fileId更新为第3版Skill62，独立下载校验通过；再次原sync-library返回current/同versionId/仍第3版，没有新增第4版。独立Skill ZIP SHA为 `ed69eb63a5d0ae9af0bd9f8dae785e9731bf3eb251fb6c273a88cd0bde85d741`。
- 默认更新器真实全新安装1.1.62、隔离旧1.1.60升级1.1.62及随后CURRENT均通过。两个Windows账号先备份再各同步8个本次路径，默认更新器均CURRENT62；无关文件字节保持。全211文件比较各202相同，另9处既有本地说明和备份/开发文档补充保留，不能称两个本地目录全量等于公开包。
- Alphabet既有研发kit沿原installer升级至62：237个manifest文件，仅9个builder-skill路径变化；原配置字节、业务容器ID、gateway/runner运行源码保持，health200且ExecStart指向新62目录，旧60目录保留。没有重发其他业务子系统。
- Codex正常原生安装/更新后为 `0.1.59-tenant.1794300638940340`、enabled，实际加载39个工具，原企业身份与connection保持；14个规范文件与同源Git/公司CI一致。WorkBuddy在原隔离Windows VM/既有5.11.3客户端通过原生Refresh由57升级59、enabled、autoUpdate=true，17个安装文件逐SHA等公司CI产物；详情页实际查看两项普通业务Skills。普通企业插件继续不内置Builder，独立开发Skill下载另行验收。未在WorkBuddy执行新的业务账号登录、付费模型调用或业务写入，不能将加载验收称为这些流程已通过。

本轮隔离Chrome配对测试使用真实生成后端SSO/session/bootstrap和两个允许父域，SaaS传输为合成环境；电脑与390px触摸模拟共4个视图通过并实际查看截图。不能把它称为真实生产员工或物理手机验收。真实Scene与SaaS公共外壳双端由各自拥有方独立记录。浏览器Back/Forward、关闭标签及全量业务写入不是本次模板发布的验收范围。

可复核命令分别为核心目录 `python -m pytest -q`、`node tests/native_template_bridge.mjs`、`quick_validate.py`，公司核心 `.ci/workflows/core-skill-ci-linux.yml`、分发 `.ci/workflows/enterprise-plugin-linux.yml` 的distribution模式，以及原 `update_skill.py --install-dir <全新目录>` / `update_skill.py`。公司日志、正式publisher回执、本地8路径备份、kit和更新器结果均由本次拥有方在本地任务审计目录保存；不向公开仓库提交凭据、业务数据或服务器连接档案。
