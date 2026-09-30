# Trusted Employee Directory Release

Owner/task: Codex / TRUSTED-DIRECTORY-RELEASE-20260930. Rules: `fa8415fc48cf9291f3c4030b69f78c33cc291a88`. This closes the Skill publication checkpoint in [the implementation handoff](2026-09-30_trusted-directory-contract.md), not downstream business deployment or data repair.

## Release And Ownership

Core 1.1.27 / [bundle-v1.4.28](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.28) was published at **2026-09-30 20:06:12 CST** from clean merged source `d9c09aac7c76d8affa440b578b0f90cba90419cc` ([PR #56](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/pull/56)). The draft's nine uploaded digests and exact target were checked before publication. No assets were replaced afterward.

The parent release task first verified SaaS source `097a867770a699c523fd90f78ba0f089766e0331`, manifest `94564e12586300f1409d3b96f73c755493514b07`, deployment 889 completed at 20:02:46 CST with controller exit 0 and all nine services at the exact expected healthy versions. SaaS owns trusted employee identity, current authorization and the directory endpoints. This Skill publication does not prove adoption by every Runtime helper or business subsystem.

The optional `employeeDirectory: true` declaration is limited to non-public create/update Actions. Ordinary 2.4/2.5 SSO and Actions remain compatible; the flag is not added to every subsystem. Backends proxy the fixed SaaS API using trusted actor/context, verify response bindings and resolve selected IDs at save time. No manual identity fallback or name-based historical claiming is allowed. Business participation and group membership remain subsystem-owned. Historical repairs require all-reference review, evidence, backup and conditional transactions while retaining scores and historical snapshots.

## Verification

- Source [PR CI](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/actions/runs/36710493789) and exact-source [main CI](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/actions/runs/36710754765) passed before the build.
- On the clean detached source, `python -m pytest -q` from the canonical core directory: **501 passed, 46 skipped in 23.24s**. `quick_validate.py` returned `Skill is valid!`. Generated-template behavioral tests are included; raw-template skips retain the boundary described in the implementation handoff.
- `python scripts/build_release.py --tag bundle-v1.4.28 --output-dir <new-private-directory>` produced exactly nine assets. ZIP integrity, safe member paths, embedded versions, catalog source/version/hash and both updater manifests matched. The other four Skill ZIPs are byte-identical to bundle-v1.4.27.
- Anonymous `curl.exe --disable --proxy http://127.0.0.1:7897 --fail --location` downloads of all nine immutable-tag assets matched the local SHA-256 values below. No GitHub authentication headers or cookies were used for these downloads.
- The unchanged downloaded `update_skill.py --install-dir <fresh-root>/zhuojian-subsystem-builder --timeout 30` returned `SKILL_UPDATED installed 1.1.27`, then `SKILL_UPDATE_CURRENT 1.1.27`. The existing installed updater returned `SKILL_UPDATED 1.1.26 -> 1.1.27`, then `SKILL_UPDATE_CURRENT 1.1.27`. These used the default Python transport through the required proxy, without monkeypatching or a replacement downloader. The previous local directory was separately backed up.
- All 154 installed files in each fresh/local core installation matched the public ZIP byte-for-byte. `update_managed_skills.py installed` reported CURRENT for SQL 1.1.2, goods 1.0.2 and NAS 1.0.3; legacy remains 1.2.0.
- Cross-repository read-only validation of the culture candidate used this merged Skill: source validation with file/object-storage flags, JSON Schema and semantic checks passed for 2.5 / 8 modules / 33 Actions / exactly three directory opt-ins. The clean final culture source `08fd9b286d6e93cb3d129680426e64197f525fd1` passed 40 focused directory/Action/SSO tests. Existing HTML fixed-width/hover and navigation runtime warnings were retained; this is not real-device or live-employee acceptance. Culture deployment and data repair remain separately owned.

## Asset Digests

| Asset | SHA-256 |
| --- | --- |
| aifabei-subsystem-builder-1.2.0.zip | `4cc7c708d5357a6626d322cd3b3d4a5212b2f5c02db30dbcf2715ce25f0f3940` |
| alphabet-daoxun-data-bridge-1.1.2.zip | `0a8667a8e34251f5468fe9f7d3f43f8b3c96a16895198ab3c46a4aafe23ec37f` |
| alphabet-goods-dashboard-handover-1.0.2.zip | `5fb6f81cd82b14f35893f5d99843af670fe4a2738cb53f308883e095d995c62f` |
| alphabet-nas-data-bridge-1.0.3.zip | `7a78812f1ad72efb517b9ad484f7b10e7ec6a209c5f45bbc784f460bf645192e` |
| catalog.json | `62a352020b794bfa95419ef7d266f3b73dbb3436919f7d09d0648fe33b5bd046` |
| update-manifest.json | `0fa5781abbb21a97b9f501f77f38f19cc8d0c8880e24ccb5e5d2ad1f15ae876d` |
| update_skill.py | `34ee9cf0a576a3ea95a2bb5031428ce1fd4cceeec2e0f4862533d9e7f4b43670` |
| zhuojian-subsystem-builder-1.1.27.zip | `47327343fa62842d22f9208e0b907203b271e604a2091c35d23193225c7e6141` |
| zhuojian-subsystem-builder-update-manifest.json | `f1d6431cf720649251c4d8900b11e9836a39c3af77e2ddf9239270c2d82ba2b4` |

## Downstream Notification

The wiki's recorded dependencies were checked before issuing one notification per affected business repository. The chairco repository's actual `manifest.json` was also checked and declares 2.3. No downstream code, roles, configuration or runtime was changed by this release task.

| Repository | Notification | Boundary |
| --- | --- | --- |
| coa | [#190](https://github.com/ZhuoJian-AI/coa/issues/190) | Only the ZhuoJian embedding/integration surface; preserve its independent toC product, assistant, gateway, identity mapping and RLS. |
| garment-production-collaboration | [#48](https://github.com/ZhuoJian-AI/garment-production-collaboration/issues/48) | Optional future directory work; no forced 2.5 upgrade, deployment or claim that unrelated material/style matching was repaired. |
| chairco-product-library | [#4](https://github.com/ZhuoJian-AI/chairco-product-library/issues/4) | Historical 2.3 needs a separately authorized compatibility assessment, not a protocol-number edit. |
| aifabei-sample-review | [#6](https://github.com/ZhuoJian-AI/aifabei-sample-review/issues/6) | Historical 2.3; no automatic template overwrite, protocol migration or deployment. |
| aifabei-production-handoff | [#6](https://github.com/ZhuoJian-AI/aifabei-production-handoff/issues/6) | Historical 2.3; no automatic template overwrite, protocol migration or deployment. |

There is no forced migration deadline. Consumers with no employee-selection requirement need no code change or deployment merely because this optional contract was released. Actual SaaS capability, current authorization and business acceptance remain the gate for adoption. The parent task owns the corresponding wiki updates; this task did not edit that repository.
