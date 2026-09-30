# Identity Acceptance Stable Release

Owner/task: Codex / IDENTITY-ACCEPTANCE-20260930. Rules: `fa8415fc48cf9291f3c4030b69f78c33cc291a88`. This closes the Skill publication checkpoint, not any downstream business repair.

## Published State

Core **1.1.28**, [bundle-v1.4.29](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.29), was published at **2026-09-30 21:09:34 CST**, from clean merged source `f95ce12e1d188e2acc49776c597aefb8680543eb` ([PR #58](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/pull/58)). Draft target, all nine uploaded digests and uploaded state were checked before publication. No published asset was replaced.

The release adds complete business-entry identity acceptance guidance, seven generated-template HTTP regressions and explicit pending identity results in pre-registration reports. It preserves trusted self-enrollment, external contacts, legitimate participation rules and immutable historical receipts. No new Manifest field, protocol migration, Runtime deployment gate or automatic business deployment is introduced. Implementation boundaries are in [the source handoff](2026-09-30_2050_identity-acceptance.md).

## Verification

- [PR CI](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/actions/runs/36718737410) and exact-source [main CI](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/actions/runs/36719156386) succeeded before the release build.
- Clean merged-source `python -m pytest -q`: **520 passed, 53 skipped in 24.03s**. Generated-template suites run through the scaffold harness; raw-template collection skips and three Windows/POSIX limitations are not counted as passes. The separate generated-project Action suite had **31 passed**. Quick validation passed.
- Independent forward scenario and code review found no blocking issue after self-enrollment and dependency-reuse wording corrections. Template Basic-header rejection is not a test of a real legacy system's valid local credentials. SaaS transport simulation is not live platform revocation acceptance. Five-table no-side-effect assertions do not independently prove filesystem residue absence.
- `scripts/build_release.py --tag bundle-v1.4.29` produced exactly nine assets from the clean merged source. ZIP integrity, member safety, embedded versions, catalog source/hashes and both updater manifests matched. The four other Skill ZIPs are byte-identical to bundle-v1.4.28.
- All nine immutable-tag assets were downloaded anonymously using `curl.exe --disable` through the required proxy, without authentication headers or cookies; each matched the local SHA-256 below.
- The unchanged public `update_skill.py --install-dir <fresh>/zhuojian-subsystem-builder --timeout 30` reported installed 1.1.28, then CURRENT. The original workstation updater reported 1.1.27 -> 1.1.28, then CURRENT. Both used their default Python transport; no downloader replacement or updater patch was required. A local backup of the preceding installation was retained.
- Each fresh/local core installation matched all **156** files in the public archive byte-for-byte. Installed Skill quick validation passed. Managed updates reported CURRENT for SQL 1.1.2, goods 1.0.2 and NAS 1.0.3; legacy compatibility remains 1.2.0.

## Asset Digests

| Asset | SHA-256 |
| --- | --- |
| aifabei-subsystem-builder-1.2.0.zip | `4cc7c708d5357a6626d322cd3b3d4a5212b2f5c02db30dbcf2715ce25f0f3940` |
| alphabet-daoxun-data-bridge-1.1.2.zip | `0a8667a8e34251f5468fe9f7d3f43f8b3c96a16895198ab3c46a4aafe23ec37f` |
| alphabet-goods-dashboard-handover-1.0.2.zip | `5fb6f81cd82b14f35893f5d99843af670fe4a2738cb53f308883e095d995c62f` |
| alphabet-nas-data-bridge-1.0.3.zip | `7a78812f1ad72efb517b9ad484f7b10e7ec6a209c5f45bbc784f460bf645192e` |
| catalog.json | `b431a2344d17673820e4069c0001b5da39c27539b94b26dfb59fc1083f216aa4` |
| update-manifest.json | `1eacbb89f8bd84b69c94132e2e2405a3d55d661a9482dab13d96510dd571b2cb` |
| update_skill.py | `34ee9cf0a576a3ea95a2bb5031428ce1fd4cceeec2e0f4862533d9e7f4b43670` |
| zhuojian-subsystem-builder-1.1.28.zip | `edf7a56871f6094fea8b3f5103a3c10b9d6bde93424fb34e6051a8ac120fa6b2` |
| zhuojian-subsystem-builder-update-manifest.json | `0bfd77ffc01175109d20e4bd524de3ded2fabe18a503d806c76b077878d98ca0` |

## Ownership And Follow-Up

SaaS remains the canonical identity/permission/directory provider. Skill owns this published development contract and tests. Each subsystem owns real business-path enforcement, person relations, forms and historical repair. This task changed no SaaS or business runtime, Runtime helper, role, local password or production record.

The organization wiki task owns publication notifications and links for the five recorded business consumers. COA notification applies only to its ZhuoJian integration surface, not its independent toC identity/assistant. Historical 2.3 consumers require separately scoped compatibility assessment. Correct implementations need no forced deployment; confirmed defects remain pending their own repair. Publication alone cannot certify other systems or close a historical identity issue.
