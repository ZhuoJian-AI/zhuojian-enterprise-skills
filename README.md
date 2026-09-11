# ZhuoJian Enterprise Skills

灼见企业 Codex Skills 的唯一公共目录。总 Skill、不同公司的服务器交接 Skill 和数据桥接 Skill 都在本仓库独立版本化，并通过同一个稳定 GitHub Release 发布。

业务负责人只需安装 `zhuojian-subsystem-builder`。首次连接一台新服务器时提供一次 `IP + root + 密码`；总 Skill 登录已初始化的 ECS 后，根据 Runtime 档案和稳定目录自动安装、更新对应交接 Skill。

历史名称 `aifabei-subsystem-builder` 保留为兼容入口。旧用户再次调用它时会自动安装并切换到新的总 Skill，不需要重新领取压缩包。公司、服务器或既有系统的特殊事实放在独立交接 Skill 中，不写入总 Skill。

稳定版只从 Release 读取，不从 `main` 安装。每次发布包含：

- 每个 Skill 的独立 ZIP；
- `catalog.json`；
- 新总 Skill 使用的 `zhuojian-subsystem-builder-update-manifest.json`；
- 旧入口兼容使用的 `update-manifest.json`；
- 首次安装使用的 `update_skill.py`。

维护与发布规则见 `AGENTS.md`。
