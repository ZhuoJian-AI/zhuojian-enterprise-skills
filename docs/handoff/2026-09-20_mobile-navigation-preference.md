# 手机模块导航偏好契约

日期：2026-09-20

## 责任与改动

SaaS 负责手机平台导航默认展开、仅显式收放、按企业与员工保存以及同浏览器窗口同步。Skill 1.1.16 将该行为和验收列为强制规范；子系统提供稳定模块 ID、名称、顺序及可见权限，不得重置平台偏好。登记完整的既有子系统无需为此重部署。

本次只修改开发规范和版本元数据；不改 Bridge、Manifest 字段、contractRevision、Runtime 或业务模板。SaaS 对应源码 PR 为 ZhuoJian-AI/ai-platform#326，发布记录在该仓库同日 mobile-module-nav-preference 交接。

## 验证

- 核心 `python -m pytest -q`：244 passed、41 skipped；跳过项不计为已完成业务/真机验收。
- `quick_validate.py skills/core/zhuojian-subsystem-builder`：通过。
- 版本测试随 skillVersion 更新至 1.1.16，契约版本仍为 2.5，兼容 2.4。

## 发布边界

PR #29 已合并为 `d1f5c659301beabd62e0a8632a020951ee237ebf`，从干净 main 构建并发布 [bundle-v1.4.16](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.16)。正式更新器无登录全新安装返回 `SKILL_UPDATED installed 1.1.16`；本机更新返回 `SKILL_UPDATED 1.1.15 -> 1.1.16`，归档身份、版本和 SHA256 均由更新器验证。

SaaS 已先发布 manifest `41534338fdb8e7fd2d91f9f0c3a84e097cc31ffd`，维护部署 `maintenance6491807ef8bd193423e3` 于 14:06:58 CST 恢复。zhangsan/lisi 真实登录的手机模拟通过首次展开、模块切换保持、刷新和新窗口恢复及跨窗口同步；九服务健康。三个现有系统有效模块登记已只读核对，本次没有业务 ECS 部署。浏览器模拟不等于真机验收；Skill 发布不等于子系统运行时已修改。
