# Runtime 平台能力发现命令（本地候选）

## 范围与基线

- 基线：`943abe7`；分支：`codex/assistant-runtime-capabilities-20260922`。
- 规则：主任务本轮取得的部署规则 `43dff14`；遵循根目录和 core Skill 的 AGENTS。
- SaaS 提供 Runtime 凭据鉴权的固定只读能力接口；本子任务只补 Skill 包中的宿主机命令、说明和聚焦测试。
- 子系统业务数据仍在各自服务器，本命令不查询其数据库、不运行模型、不创建 Task、不执行业务 Action。

## 实现

新增 `zhuojian-runtime platform-capabilities`：

1. 检查固定 Runtime 档案为普通文件、root 所有且不可由组或其他用户写入（Windows 开发测试保留已有 owner 兼容规则）。
2. 必须有明确且合法的 HTTPS `platform.baseUrl`；命令不接受 URL 参数，不使用默认目标补猜。
3. 复用现有固定 root-only Runtime 注册凭据，只发送一次 GET 到 `/api/v1/ecs-publisher/platform-capabilities`；禁用环境代理和全部重定向，不将凭据传给子进程。
4. 限制响应为 16 KiB，校验协议版本、已知契约版本、固定能力语义及强制免责声明后重新构建白名单输出。未知字段不输出，不展示任意错误响应体。
5. 404 表示当前部署未提供发现能力，结果仍未知且退出码为 2；撤权、网络错误、超限及未知协议同样不返回成功。

固定协议只描述实现支持，不能证明员工获权、企业配置、下游就绪或业务验收。`backgroundDelegation` 与 `unattendedExecution` 必须明确为 false；以后改变协议语义需同步命令，不默认推断支持。

没有修改已有注册、发布、回滚等命令。没有复用会默认跟随 HTTP 重定向的既有发布请求函数；新命令独立使用拒绝重定向处理器。

## 验证

在 `skills/core/zhuojian-subsystem-builder` 运行：

```text
python -m pytest -q tests/runtime_host/test_platform_capabilities.py tests/runtime_host/test_runtime_admin.py assets/admin-runtime/host/tests/test_runtime_admin_host.py
```

结果：**120 passed，1 skipped**（Windows 不支持的既有测试）。全部网络请求均为本地模拟，未连接实际 SaaS 或 ECS。

覆盖固定目标、单次 GET、凭据不输出、不启动子进程/本地写入、禁代理/重定向、HTTP 404/401/403/429/5xx、网络超时、无效/超大响应、嵌套白名单、错误版本、假授权保证、恶意端点、未知后台执行语义、档案权限、凭据换行注入及 CLI 成功/失败退出码。

`quick_validate.py .`、`git diff --check` 和 `platform-capabilities --help` 均通过。

## 发布边界

本记录仅证明候选源码与隔离测试完成，不证明线上接口已部署。不推送、不创建 Release、不在 ECS 安装宿主机 helper。开发 Skill 更新不能自动更新已有 `zhuojian-runtime`；未安装新版 helper 的服务器不会出现新命令。是否发布及下游升级由主任务统一处理。
