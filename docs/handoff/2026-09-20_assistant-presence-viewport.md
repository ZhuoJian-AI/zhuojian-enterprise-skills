# 业务助手轨迹视口夹紧补丁

日期：2026-09-20；目标版本：core 1.1.15 / `bundle-v1.4.15`。

## 原因与修正

- Chromium 手机视口实测发现：当锚点高度超过一屏且锚点顶部不为 0 时，旧算法只限制 `height <= innerHeight - 4`，没有扣除 `top`，边框底部仍可能超出 iframe 视口。
- 新算法分别按 `innerWidth - left - 2` 与 `innerHeight - top - 2` 计算剩余空间；AI 圆点移入边框，短状态使用视口固定安全区位置。
- 仍为 `pointer-events:none`；消息白名单、Origin/source/nonce/应用/模块/页面校验、完整助手文字和契约 2.5 均不变。

## 发布状态

当前为待测试候选。合并后必须从干净 `main` 构建不可变 Release，验证公开安装与正式更新器；Skill 发布不能替代三个业务子系统的代码、部署与线上验收。
