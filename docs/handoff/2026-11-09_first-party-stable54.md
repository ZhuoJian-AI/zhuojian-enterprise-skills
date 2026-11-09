# core1.1.54 第一方稳定分发

公共源码PR115合并为2d7abcb51178b171e06c7a56a9f2367baf307c7f，源码tag为bundle-v1.4.59。公司Linux完整core1039通过、60跳过；Windows相关core946通过、7跳过。路由fixture隔离后台恢复线程，POSIX测试使用短临时目录以满足Unix socket路径要求。

稳定入口为 https://ai-platform.staging.zhuojianai.com/enterprise-plugin/updates/latest.json 。独立Skill使用skillUpdates/skillCatalog；插件0.1.39和core1.1.54各自版本独立。归档由公司CI1794213011743509从锁定公共main构建，随SaaS独立静态发行plugin-0139-company-20261109激活。没有上传GitHub Release资产，旧公开对象和下载均保留。

真实HTTPS校验24个路径及POST拒绝/404通过。未指定测试传输、URL或DNS覆盖的默认更新器，全新安装1.1.54成功；codex02和王鑫涛两份本地安装均CURRENT1.1.54、quick_validate通过。本地以三方合并保留既有扩展，不声称整树等于公共ZIP。Alphabet服务器开发kit更新为1.1.54，配置逐项保持一致、服务运行；既有12个业务子系统没有在本次Skill发行中重新部署。

通用问题、Cookie双通道与实时鉴权要求见Skill的references/browser-session-cookies.md。子系统主责业务会话Cookie；SaaS主责统一身份/授权/外壳；Skill负责模板与验收。不能把平台launch成功等同业务登录成功，也不能因手机401直接扩大员工权限。兼容补丁已分别部署到Alphabet12系统，真实张琳手机钉钉复验仍待完成；不把浏览器手机尺寸模拟当真机。

完整SaaS分发与后端内嵌模板状态以ai-platform的docs/handoff/2026-11-09_skill-cookie-formal-distribution.md及实际发布回执为准。其他企业运行时不会因安装Skill自动更新。
