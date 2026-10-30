# zhuojian-enterprise-skills：公司 CI 迁移

本仓负责同步 CI 声明和原有检查；自有执行器、核权、结果/制品存储与发布适配由 zhuojian-server-deploy 主责。GitHub 只保存源码，不增加 Actions/Artifact/GHCR 预算。源码改动经 [PR110](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/pull/110) 审查；本页和配置同时发布，main SHA 及后续复测以真实回执为准。

现行入口是 `.ci/project.json` 与下列工作流；旧 `.github/workflows` 保留兼容/审计，组织与仓库 Actions 已关闭。原项目测试保留，失败不能用核权成功代替。公司主机不增加 CPU、内存、swap、PID、线程、堆、I/O 配额或固定全局并发门禁，AI 可使用既有 SSH/sudo/Docker 调试。

- `.ci/workflows/core-skill-ci-linux.yml`
- `.ci/workflows/handoff-ci-linux.yml`

完整日志、源码镜像、运行时缓存、制品与镜像留公司 CI。生产主机只按具体发布请求读取小型回执、远端日志摘要和指定制品/镜像，不批量复制日志或源码缓存。生产仍经原登记发布入口；本轮没有重新部署或重启本仓业务服务，没有改动业务数据和授权。

Windows 安装脚本仅在开发人员 Windows 电脑按需验证，不常驻公司 Windows CI，也不是每次 Linux CI/发布的固定前置条件。

## 实际验证与边界

自有 CI 基础链路已在公司完成真实并行制品往返、不同任务工作区隔离及缓存保留；新增原生测试服务经过两个真实 PostgreSQL、不同回环随机端口、SQL 及归属清理验证（手动 run `1793341149328196`）。主服务器与 COA 的实际发布器均核验公司 main 回执、下载并核对 7,804 字节制品，并拒绝真实失败回执；两个宿主经只读隧道实际接收公司不可变测试镜像，未启动业务容器。详细证据见 [部署 Skill 交接](https://github.com/ZhuoJian-AI/zhuojian-server-deploy/blob/main/docs/handoff/2026-10-30_own-ci-migration.md)。

以下是本仓迁移期间已取得的原始回执快照，包含失败与未完成项；不是对最新 main 或所有业务测试通过的声明。早期执行器的 Python 别名、工作目录、临时服务和缓存问题已另行修复，后续 run 保留自己的源码与执行器摘要，不覆盖旧结果。

| 自有 run | 源码 | 工作流 | 分支 | 当时状态 |
| --- | --- | --- | --- | --- |
| 1793335995196515 | `bd0a15e2e796` | `.ci/workflows/core-skill-ci-linux.yml` | `refs/heads/feat/own-ci-20261030` | failed |
| 1793339282000970 | `bd0a15e2e796` | `.ci/workflows/handoff-ci-linux.yml` | `refs/heads/feat/own-ci-20261030` | success |

失败或未完成仍阻止对应生产发布；后续由公司 CI 对 main 的真实变化触发检查，不回退 GitHub hosted，不放宽断言，也不将源码合并当作生产验收。
