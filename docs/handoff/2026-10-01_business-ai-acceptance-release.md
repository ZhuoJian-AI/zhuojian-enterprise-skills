# Business AI Acceptance Stable Release

Owner/task: Codex / AI-BUSINESS-ACCEPTANCE-20261001. This records Skill publication only, not SaaS, Runtime or business-subsystem deployment.

## Published State

Core **1.1.29**, [bundle-v1.4.30](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.30), was published at **2026-10-01 22:32:29 CST**, from clean merged source `a7caac9b299f27573156990711e2c5c2d1464c20` ([PR #60](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/pull/60)). The draft target and all nine uploaded asset states/digests were verified before publication. No published asset was replaced.

This release adds conditional evidence-based acceptance for actual business completion, persistence/streaming, current source context, real file/version receipts and partial visual coverage, business relations and historical-source/DLP boundaries, and cold/warm business-first-screen timing with authorization revocation. It prescribes neither fixed business answers nor a mandatory tool trajectory. Supported contracts remain 2.4/2.5, with new-project default 2.5. Templates, Schema, updater, release builder, catalog selectors and the four other Skill source trees are unchanged. See [the source candidate handoff](2026-10-01_business-ai-acceptance.md) for implementation and earlier offline smoke evidence.

## Verification

- [PR CI](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/actions/runs/36876270156) and exact-source [main CI](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/actions/runs/36876638186) succeeded. The main workflow reported an upstream Node action-runtime deprecation annotation; it was not a test failure or changed by this task.
- Clean merged-source Python 3.10.11 `python -m pytest -q`: **522 passed, 53 skipped in 27.26s**. Skips are three Windows/POSIX ownership/mode limitations and 50 raw-template route tests that run only in a generated project. They are not counted as tested by collection alone. The two new acceptance regressions and core quick validation passed; candidate link checks resolved 42 local links.
- The original `scripts/build_release.py --tag bundle-v1.4.30` produced exactly nine assets from clean merged source. All five ZIP CRCs, member paths, embedded versions, every packaged tracked file byte comparison, catalog source/hashes and both updater manifests matched. The formal core ZIP contains 156 tracked files. The earlier feature-branch offline smoke archive is not a formal Release asset; its digest must not be used for this publication.
- The preceding `bundle-v1.4.29/catalog.json` was independently downloaded anonymously. All four unchanged Skill ZIP digests matched that stable catalog. The public updater bytes also match the original source.
- All nine immutable-tag assets were downloaded anonymously using `curl.exe --disable` through explicit required proxy, without authentication headers or cookies; each matched the local SHA-256 below. The actual remote tag resolves to `a7caac9b299f27573156990711e2c5c2d1464c20`.
- The public original `update_skill.py --install-dir <fresh>/zhuojian-subsystem-builder --timeout 30` reported installed 1.1.29, then CURRENT. The workstation's original updater reported 1.1.28 -> 1.1.29, then CURRENT. Both used the unchanged default Python transport; no downloader bridge, updater patch, TLS exception or global proxy modification was used. A private local backup of the prior installed core was retained.
- Each fresh/local core installation matched all **156** public archive files byte-for-byte. Installed Skill quick validation passed. The new version metadata, matching changelog, SKILL and affected reference were reloaded. Managed update reported CURRENT for SQL 1.1.2, goods 1.0.2 and NAS 1.0.3; legacy compatibility remains 1.2.0.

## Asset Digests

| Asset | SHA-256 |
| --- | --- |
| aifabei-subsystem-builder-1.2.0.zip | `4cc7c708d5357a6626d322cd3b3d4a5212b2f5c02db30dbcf2715ce25f0f3940` |
| alphabet-daoxun-data-bridge-1.1.2.zip | `0a8667a8e34251f5468fe9f7d3f43f8b3c96a16895198ab3c46a4aafe23ec37f` |
| alphabet-goods-dashboard-handover-1.0.2.zip | `5fb6f81cd82b14f35893f5d99843af670fe4a2738cb53f308883e095d995c62f` |
| alphabet-nas-data-bridge-1.0.3.zip | `7a78812f1ad72efb517b9ad484f7b10e7ec6a209c5f45bbc784f460bf645192e` |
| catalog.json | `710397217190e16d56f17ed299e04fff398f172c89dea7d5da9b3deb7948cf0c` |
| update-manifest.json | `709696571fcc78dabacddda5818316110d44cbbabdddd148adee0a58c3b19105` |
| update_skill.py | `34ee9cf0a576a3ea95a2bb5031428ce1fd4cceeec2e0f4862533d9e7f4b43670` |
| zhuojian-subsystem-builder-1.1.29.zip | `06c98f6c0e390d9a8f7d2176aef14199b22b1daa18d6655d8157f1049666d8d4` |
| zhuojian-subsystem-builder-update-manifest.json | `30d5251766ce2ec59fdc9884e6e734c29567476df2ef6d7a5e3dae850880fcf8` |

## Ownership And Remaining Work

SaaS owns public assistant orchestration, output, context, file/artifact delivery, permissions and shared startup; each subsystem owns business facts, relationships and local initialization. Skill owns only this published development/acceptance contract. This publication did not modify or deploy SaaS, Runtime helpers, business services, roles, permissions, DLP or source data, and does not certify any untested employee workflow or physical device.

Unavailable source evidence, partial extraction, uninspected pictures/media, unresolved runtime dependencies and unmeasured loading remain explicit open work in the affected private project. A structurally readable presentation is not proof of image comprehension; a tool's auxiliary success is not the user's completed goal. Correct existing implementations do not require forced deployment or protocol migration solely because the Skill updated. Organization wiki records the verified milestone separately.
