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

候选待合并后从干净 main 构建 bundle-v1.4.16；稳定包、公开安装与本机更新成功后补充证据。Skill 发布不等于子系统运行时已修改。
