# 现有运行与数据线索

来源：2026-11-13获权 SSH、平台只读登记查询与本人页面观察。这里不包含业务记录、账号映射、凭据或可执行的固定修复顺序；现场最新结果优先。

## 运行方式与实际数据

观察时网页采用专用发布器的冻结版本；collection 数据服务还存在从 /home/ssqc02/projects/ssqc-worktrees/collection-web-import-20261113 启动的实例，引用项目旁 .ssqc-collection-private/acceptance/config.json。虽然目录叫 acceptance，它承载了真实已导入的业务数据，不是可清理的临时库。另有旧冻结 worker，需要按实际启动参数和配置定位读写归属，不按目录名称猜测。

webimport 有每5分钟调用 .ssqc-collection-private/webimport/service.sh start 的 cron，不能仅凭非 systemd 就断言没有持久拉起。也不能仅凭 cron 存在认为网页、数据服务、配置和冻结版本已统一发布。用本次实际服务证据判断。

Runtime /etc/zhuojian 和 /usr/local/sbin/zhuojian-runtime 是受保护位置。普通 ssqc02 读取可能返回 PermissionError；平台已登记 Runtime，完整 doctor/初始化验收需要相应权限，业务健康里的 runtimeInitialized 不足以判定整机状态。

## 曾出现的问题与可核验证据

2026-11-13曾出现数据已导入、网页已恢复部分显示，而平台仍保留旧页面目录的情况。直接原因之一是新增页 aiSemantics.relatedPages 使用字符串，平台协议要求包含 moduleKey、pageKey、relationship 的对象。以实际校验错误和平台生效 Manifest 判断当前状态，不把 health200 或发布器一句成功当作同步完成。

导入曾出现 HR 视角进入人员导入分支、按钮又被只读逻辑禁用的问题。核对具体业务目标、本人当前能力、按钮分支与服务端授权；不要为修前端自动扩大整个 HR 角色的导入权限。

新 SaaS 用户曾在入口签发成功后被旧系统本地业务岗位映射拒绝。另一独立学院应用也曾有允许来源与实际 SaaS 域名不一致。分别核对实际账号、企业、来源、SSO、业务关联；不要把平台注册失败、插件连接失败和子系统关联缺口混为一谈，也不要将企业管理员自动映射成任意业务身份。

用户页面、写入/导入、平台同步及手机流程按本次承诺分别记录。本文不宣称这些问题当前仍存在或已经解决；新代码、真实结果与未测项保存在项目交接，以避免下一位 AI 把旧快照当作现状。
