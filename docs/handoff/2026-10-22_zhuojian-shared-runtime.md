# 灼见共享 Runtime 交接候选

企业 Runtime `zhuojian-hz-shared-01` 已登记。只读审计确认企业/Runtime 匹配、登记凭证 root-owned 0600、通用 doctor 未安装、`initialization.ready=false`。标准主机安装器依赖的 Nginx 与现有 80/443 独立 Traefik 冲突，直接构建/部署也不符合原 Lab 的登记 CI/SSH 发布边界。

本变更新增仅匹配该 Runtime 或该公网主机的交接 Skill，保留原服务、数据和源绑定发布；不改总 Skill、安装器或其他企业包。它记录准确 pending 和继续验收条件，不能表示 Runtime 完整初始化或原生 Lab 已上线。

验证：逐 Skill quick_validate；原始 package/updater 的本地 ZIP、精确 Runtime/host 空目录安装与逐文件比较、企业名/其他 Runtime 不命中；主机只读 audit；秘密扫描与 diff check。这里的本地传输 fixture 不属于稳定 Release 的无缓存公开解析。

后续门槛：reviewed PR 合并；从干净 main 构建未占用的下一 bundle，发布所有不可变资产及摘要；对公开稳定目录执行无缓存 Runtime/host 解析、逐文件比较并同步本机。发布前均为“交接 Skill 尚未对业务负责人可用”。完整主机适配、备份、双应用与员工 SSO/双端验收另行记录，不借文档版本关闭待办。
