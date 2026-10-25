# Alphabet 源服务器退役的公司交接更新

状态：**源实例已退订，资源已释放；公司包待发布**。主执行者已取得2026-10-25 12:36:40 CST的退订订单及供应商退款成功回执，12:40:57完整杭州实例清单已确认旧实例消失。迁移及前轮稳定发布事实见[已完成迁移交接](2026-10-25_alphabet-consolidation-actual.md)。

## 范围

唯一源云实例为 `cn-hangzhou` / `13061953402a4a2982a041a6b911d04f`，历史 Runtime `aifabei-hk-48` / `5ebee1b5-57da-4c97-9f97-a595fb4c63ed`。现役仍为 `47.97.90.161` / `aifabei-hk-01`，运行九应用；两个原 `hk48` 网址、App UUID、数据和授权不变。NAS 与道讯原始资料继续在公司内网，云实例退役不代表这些设备或原始资料被删除。

本次仅更新Alphabet的三份公司交接与活跃选择器：

| 公司 Skill | 当前稳定 | 待发布补丁 | 更新内容 |
| --- | --- | --- | --- |
| alphabet-daoxun-data-bridge | 1.1.3 | 1.1.4 | 源退役边界；现役 SQL 路径保持 |
| alphabet-goods-dashboard-handover | 1.0.3 | 1.0.4 | 源不再可供恢复/转发；机外恢复位置与员工验收边界 |
| alphabet-nas-data-bridge | 1.0.4 | 1.0.5 | NAS 旧源连接收口及现役读取证据 |

版本已写入候选源码，尚未发布稳定目录或资产。通用Builder core1.1.44、legacy1.2.0和共享主机交接1.0.0不变；本次不修改通用接口、模板或授予新的业务权限。NAS随包脚本只撤三处旧48 start/stop/status调用及更新注释，必须与Root实际安装的同源候选一致。

## 待完成的回执

- [x] 源历史124文件全部机外逐SHA覆盖；Windows E盘116文件，管理员受限归档补齐8文件，最新恢复点/Windows ACK另有证据。
- [x] NAS旧48分支已撤除，原01进程保持，目标最终NAS应用容器四共享读取通过；设备错误系统时间不用于本次执行日期。
- [x] 云实例已退订、供应商退款成功；目标九应用9/9 health200。资源已于12:40:57在完整杭州实例清单中核验释放。
- [x] 更新三份公司Skill当前环境、CHANGELOG和skill-version；保留有日期的历史，停止建议连接旧IP。
- [x] catalog仅撤销该旧IP与旧Runtime的活跃匹配；当前目标匹配与历史审计身份保留。
- [x] 三份官方quick_validate、公司4项既有测试、原生managed updater当前host/runtime匹配三包、旧host/旧runtime/仅企业名不匹配共5组，以及实际安装包逐文件比对通过；NAS脚本与已安装候选字节相同、bash语法及diff检查通过。未用本地file目录验证冒充公开Release验收。
- [ ] 正常PR/main合入、新稳定bundle和匿名目录/更新器验证；未变包复用前版字节。
- [ ] 主执行者按授权限定同步两个人账号，校验改动文件及无关文件保持；本草稿作者不修改个人目录。

商品看板的正常员工 SSO 电脑业务验收已完成；手机390视口展示/菜单和 DOM 点击筛选有证据，坐标点击失败原件保留，未验真机或触摸。该验收仅属于实际看板路径，不把九应用 healthy 当作全部业务流程通过。

中央服务器事实以[部署台账](https://github.com/ZhuoJian-AI/zhuojian-server-deploy/blob/main/references/server-project-inventory.md)及其有日期回执为准。当前公开稳定仍bundle-v1.4.46/source `bc4551ed67f6e5f6aa59928eb016172c44aeb922`；本隔离工作树未push/merge/release，不能要求其他负责人已经安装新补丁。core/legacy/shared在新bundle复用46原ZIP字节，不为单企业退役提高通用契约版本。
