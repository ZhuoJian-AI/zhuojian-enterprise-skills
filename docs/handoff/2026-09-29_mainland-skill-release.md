# 杭州迁移 Skill 稳定发布验收

2026-09-29 01:38:21 CST，[bundle-v1.4.25](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.25) 从干净合并源码 `af6f004923182a6b9ae9c6afd2ff060ca4cd581c`（PR #50）正式发布，非 draft/prerelease，设为 latest。

版本：core `1.1.25`、道讯 `1.1.1`、商品动销 `1.0.1`、NAS `1.0.2`；兼容入口保持 `1.2.0`。九个资产均通过匿名公开下载 SHA-256 核验；兼容 ZIP 与上版保持 `4cc7c708d5357a6626d322cd3b3d4a5212b2f5c02db30dbcf2715ce25f0f3940`，core ZIP 为 `5bdf28262764eea9f73982ab8a311417394433f29698cc074c80fed25bfcfbd3`。

公开原始更新器全新安装及重复 CURRENT 通过；本机 core `1.1.24 → 1.1.25`、三个已安装公司包更新和重复 CURRENT 通过。本轮使用既有 7897 代理和原始 Python 下载实现，没有替换传输、摘要检查、安全解压或原子安装。旧安装目录已另存可恢复副本，SSH 档案及凭据不在 Skill 目录内，未改动。

按实际 `enterpriseKey=aifabei`，分别对 `aifabei-hk-01 / 47.97.90.161` 和 `aifabei-hk-48 / 101.37.173.94` 执行无缓存 managed resolve，匹配预期企业包且全部 CURRENT。本机四包逐文件与公开归档相同，分别核对 153、7、6、5 个文件，四份 quick_validate 通过。更新后已经重读入口和相关环境参考。

实现来源 PR #47 的核心与迁移恢复测试、CI 通过；本次最终事实 PR #50 只变更 handoff/公司参考，仓库唯一 CI 的 core 路径过滤不触发，并未虚报该 PR 跑过 CI。两份公司参考的校验及 diff 检查通过。

部署规则独立仓库已合并杭州实际入口；本机 `灼见服务器部署` 仍是上游指针壳，原 fetch_rules.py 拉到 `eb85656` 且 `STUB_OK=1`。该壳以后继续每次拉最新规则，不把本地审计副本当稳定规则来源。

服务器与员工流程的真实结果、桥接及未完成项见 [接管交接](2026-09-29_mainland-active.md)。本稳定发布不会替代运行时验收：企业内网仍经香港临时桥，生产协同既存手机 overflow 未在迁移修复；主机本地全量备份已验证，专用 OSS 凭据手机验证和首次 OSS 整份读回仍待完成。后续部署规则可补新的备份证据，不能因本包发布提前宣称成功。
