# Alphabet 源服务器退役的公司交接更新

状态：**源实例已退订释放；三份公司包已公开并完成两账号限定同步**。主执行者已取得2026-10-25 12:36:40 CST的退订订单及供应商退款成功回执，12:40:57完整杭州实例清单已确认旧实例消失。迁移及前轮稳定发布事实见[已完成迁移交接](2026-10-25_alphabet-consolidation-actual.md)。

## 范围

唯一源云实例为 `cn-hangzhou` / `13061953402a4a2982a041a6b911d04f`，历史 Runtime `aifabei-hk-48` / `5ebee1b5-57da-4c97-9f97-a595fb4c63ed`。现役仍为 `47.97.90.161` / `aifabei-hk-01`，运行九应用；两个原 `hk48` 网址、App UUID、数据和授权不变。NAS 与道讯原始资料继续在公司内网，云实例退役不代表这些设备或原始资料被删除。

本次仅更新Alphabet的三份公司交接与活跃选择器：

| 公司 Skill | 前版 | 当前稳定 | 更新内容 |
| --- | --- | --- | --- |
| alphabet-daoxun-data-bridge | 1.1.3 | 1.1.4 | 源退役边界；现役 SQL 路径保持 |
| alphabet-goods-dashboard-handover | 1.0.3 | 1.0.4 | 源不再可供恢复/转发；机外恢复位置与员工验收边界 |
| alphabet-nas-data-bridge | 1.0.4 | 1.0.5 | NAS 旧源连接收口及现役读取证据 |

三份补丁已随bundle-v1.4.47公开。通用Builder core1.1.44、legacy1.2.0和共享主机交接1.0.0不变，三个未变ZIP复用46原字节；本次不修改通用接口、模板或授予新的业务权限。NAS随包脚本只撤三处旧48 start/stop/status调用及更新注释，与Root实际安装的同源候选字节一致。

## 实际回执

- [x] 源历史124文件全部机外逐SHA覆盖；Windows E盘116文件，管理员受限归档补齐8文件，最新恢复点/Windows ACK另有证据。
- [x] NAS旧48分支已撤除，原01进程保持，目标最终NAS应用容器四共享读取通过；设备错误系统时间不用于本次执行日期。
- [x] 云实例已退订、供应商退款成功；目标九应用9/9 health200。资源已于12:40:57在完整杭州实例清单中核验释放。
- [x] 更新三份公司Skill当前环境、CHANGELOG和skill-version；保留有日期的历史，停止建议连接旧IP。
- [x] catalog仅撤销该旧IP与旧Runtime的活跃匹配；当前目标匹配与历史审计身份保留。
- [x] 三份官方quick_validate、公司4项既有测试、原生managed updater当前host/runtime匹配三包、旧host/旧runtime/仅企业名不匹配共5组，以及实际安装包逐文件比对通过；NAS脚本与已安装候选字节相同、bash语法及diff检查通过。未用本地file目录验证冒充公开Release验收。
- [x] [PR89](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/pull/89)正常合入 `41fb1cac6f3fe90ba20eb355e19852d79f854d53`，PR/main检查成功；[bundle-v1.4.47](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.47)于2026-10-25 12:48:06 CST公开，Release ID `423153399`。十个匿名资产SHA、四个latest入口、八组selector、三份公司包原生fresh/CURRENT均通过；未变包保持46原字节。
- [x] Root先备份/CAS后，将三份公司Skill共13个受影响路径分别限定同步至codex02与王鑫涛账号，每账号13路径。两边实际SHA及版本核对通过、范围外文件保持；没有整目录覆盖或为其他负责人电脑自动安装。

商品看板的正常员工 SSO 电脑业务验收已完成；手机390视口展示/菜单和 DOM 点击筛选有证据，坐标点击失败原件保留，未验真机或触摸。该验收仅属于实际看板路径，不把九应用 healthy 当作全部业务流程通过。

中央服务器事实以[部署台账](https://github.com/ZhuoJian-AI/zhuojian-server-deploy/blob/main/references/server-project-inventory.md)及其有日期回执为准。服务器详情12:42自然更新9台、failed/excluded均0；费用12:45自然更新阿里云6+Zoro3，Root正常Console看到9台且旧源消失。费用整体仍有原有DeepSeek partial，不由本次服务器退役宣称全部模型账户健康。

本段实际发布证据由后续docs-only提交记录，不改包内Skill或catalog、不重打已发布bundle。匿名回执为本机 `r47public/public.actual.json`，限定同步为 `r47sync-apply/sync.actual.json`；只记录经过验证的状态，不把本机双账号同步推定为Alphabet其他负责人的电脑已经更新。
