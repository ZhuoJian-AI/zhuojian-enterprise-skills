# 现有 Runtime 接入原系统人员同步

主责：SaaS 提供公共接口、授权和原员工生命周期；企业采集程序适配来源；本 Skill 提供按需接入知识和可选投递工具。保留 SaaS 手工管理、现有正常同步、员工角色与历史归属。不自动迁移企业、不重发业务子系统。

core1.1.63 候选补充 `references/personnel-sync.md`、知识导航、Python标准库投递工具与可选systemd模板；Runtime投影识别平台实际声明的 `personnelSync`。普通企业插件沿原动态管理员通道发现五项来源管理操作，不复制一套插件登录或权限。SaaS配套源码 PR1231；Skill安装不等于其已部署。

工具与 SaaS `deploy/enterprise-directory/directory_sync.py` 同源，覆盖来源身份绑定、原ID版本、持久化待发批次、丢失回执后原请求重传和来源缺失不推断离职。企业专用数据库结构、凭据、主机和业务数据不进核心 Skill。

## 正式发行与当前边界

PR133/main e12bef8b0f9194a44b9cf86d73bcf3f0c22a81d3，core1.1.63/tag bundle-v1.4.69。公司候选1794878976773654、精确main1794879266265711均成功，每轮1063 passed/65 skipped、maintenance24 passed；Windows最终1042 passed/86 skipped，定向215及quick_validate通过。

SaaS PR1231/1238已合并，独立Skill216文件及两份baked模板同源。静态发行0.1.60由公司1794879615272834/source6eebe068通过包162项/固定发布器/实际只读Nginx检查；原受保护静态入口stage/prepare/activate为plugin-0160-company-20261117。1687公开对象保留全部1655旧对象，36个变更文件HTTPS200/SHA通过。原文件库同fileId第4版Skill63已下载验证，再sync为current，未新建第5版。

默认更新器实际全新安装63、旧60→63和随后CURRENT、两个真实账号CURRENT63全部通过；旧60不可变URL仍200/SHA不变。两个Windows先备份再各同步12路径、仅新增5文件；SKILL原本地说明链接和其他无关文件保持。Alphabet现役研发kit经原installer更新63、242清单文件/13个Builder路径变化，gateway/runner执行代码、配置字节及业务容器保持，health200/新ExecStart核对通过，旧62保留。未安装人员同步timer或修改员工。

主机静态发布器曾因内核设备号变化拒绝，已核对真实挂载身份和全部历史文件，备份后仅刷新对应登记，原guard恢复；不移除检查。非秘密维护定位及精确回执保存在两账号本地关键数据Wiki，不向本公共仓库复制机器恢复资料。

SaaS业务API仍待0098增量迁移、兼容回退/Control配对和原受保护发布；已通过的正式后端Maintenance1794880083820464/567项不代表已上线。原业务插件Skills与连接工具内容未改，静态60包可下载；本聊天实际原生加载仍59，WorkBuddy60自然升级及热刷新未验，不能冒称所有客户端已更新。SaaS实际baked下载也随业务后端上线另验。两家企业原正常同步不迁移，真实来源授权、可信映射及自动事件送达单列，完整状态见[SaaS交接](https://github.com/ZhuoJian-AI/ai-platform/blob/main/docs/handoff/2026-11-16_enterprise-directory.md)。
