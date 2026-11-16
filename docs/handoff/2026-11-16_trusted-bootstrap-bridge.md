# 原生模板可信bootstrap与Bridge

Builder1.1.61修复原生模板用document.referrer推断父平台Origin的问题。已鉴权后端bootstrap返回的平台HTTPS Origin是唯一绑定来源；不从URL/referrer补授权。保留消息父窗口、来源、应用、nonce、模块和页面的原协议校验，ready仍是原四字段，不新增协议。

ready表示可信上下文和实际可交互界面已呈现，不代表所有业务查询成功。初始读取使用当前页面actionKeys：query-only读取，write/upload-only不先查询才能进入；查询或文件读取错误单独显示。可选SDK独立加载，迟到导航SDK在真实视图已就绪时重新协商；不注入假host-ready或解除父DOM/inert。刷新复用真实草稿判断，不重读覆盖未提交输入。

开发电脑实际执行模板内联JS及原navigation SDK的行为回归通过：缺失/自身/错误referrer、无效bootstrap Origin拒绝、伪造父窗口/来源/app/nonce/module/page拒绝、SDK失败/迟到、query-only与write/upload-only、无files/读失败仍可操作、刷新幂等与文件/AI输入/草稿deferred。生成模板和现有导航专项9项通过，quick_validate通过。全量公司CI、正式包、默认更新器、两Windows、SaaS内嵌、服务器kit及客户端状态仍待后续回执，不以源码修改冒称完成。

SaaS后端的development_skill_templates.json由受保护development-skill下载直接读取，随backend镜像COPY入包，须另外沿原受保护入口发布；普通业务插件不嵌Builder。现有业务子系统不因本次Skill更新自动重发，业务验收继续单列。
