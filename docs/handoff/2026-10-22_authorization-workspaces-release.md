# Core 1.1.39 stable release

Published at 2026-10-22 12:31:24 Asia/Shanghai.

- Source PR: [77](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/pull/77).
- Clean merged main: `267ab0847d668ffeb75c2280438ea1b4bcf841b0`.
- Exact PR CI: [39722249386](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/actions/runs/39722249386), success on `7cc360ccbbea769707eb0c56d4bfd7b49b96e86a`.
- Exact main CI: [39722540328](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/actions/runs/39722540328), success on the release source.
- Release: [bundle-v1.4.40](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.40), core `1.1.39`, revisions `2.4/2.5` preserved.
- Final local suite: 607 passed, 56 conditional skips, one existing anyio deprecation warning. Generated-project route/security/recovery, focused tests and Skill validation passed.

The first PR CI found the old release-version assertion (one failure, 606 passed). It was corrected and the complete final source passed again locally and in both exact CI runs; the red run is not counted as successful validation.

## Fixed boundaries

The explicit `management/workspaces` policy binds each Action to employee D0 plus departments contributed by that Action's independently granting active roles. No default department or grant means no invented all-enterprise authority. Wire scope remains the existing department ID list. Personal, public, shared and legacy configurable boundaries are preserved unless explicitly adapted and verified.

Starter behavior preserves record departments, rejects broad fixed-workspace scopes and allows specialized routes to set a server-owned exact context. Import create/update scopes and atomicity, source ownership, department lifecycle, old sessions/tickets and web/API/AI/file/export revocation remain required runtime acceptance. Technical preflight emits pending checks rather than a false success.

Before registering the new mode, every actual SaaS consumer must support it. Restore old downstream Manifest endpoints and officially registered metadata before rolling back old consumers. This Skill release did not register customer Manifests, change employee grants or deploy SaaS/Runtime/business systems; those release owners must report their separate evidence.

## Public distribution

The package was built from the clean merged source in an LF checkout. The four unrelated archives were copied byte-for-byte from the preceding official bundle and the new catalog/legacy update manifest were recomputed to those verified hashes; unchanged Skill versions were not repackaged under different bytes. No previous Release was replaced.

| Archive | SHA-256 |
|---|---|
| zhuojian-subsystem-builder-1.1.39.zip | `3b1acafdd1b27aca2ccdc011274c96caa79d5253d7ce66988d933211d72198e0` |
| aifabei-subsystem-builder-1.2.0.zip | `31a542a2af48a81ff97a103c3e729a7c75d1aaab029e2d2d8af821546b7181ea` |
| alphabet-daoxun-data-bridge-1.1.2.zip | `4eb6b6b56616fba08943fa1bd2914be9ac1aa0af73599c010f5df823d0982237` |
| alphabet-goods-dashboard-handover-1.0.2.zip | `8fcb6f4481cd17784bb59bd88b9fcf4112a3b915b1adc3726293fa4df7976067` |
| alphabet-nas-data-bridge-1.0.3.zip | `63d05f1ad39764bcd9aa39d1be5febe614fc5ce92a31474d91e0d192600f3437` |

All nine public assets were anonymously fetched with cache bypass and matched the local release SHA-256. The original published updater, its default latest URL and original urllib transport produced:

```text
SKILL_UPDATED installed 1.1.39
SKILL_UPDATE_CURRENT 1.1.39
SKILL_UPDATED 1.1.38 -> 1.1.39
SKILL_UPDATE_CURRENT 1.1.39
```

Both fresh and upgraded installs matched all 163 public archive files. An initial upgrade attempt in an overly long Windows artifact path hit the existing path-length limit; its failure receipt is retained. A short isolated directory completed all four original-updater checks without changing OS settings, transport or updater code.

## Personal installation and existing systems

Only the 20 packaged paths changed by this PR were backed up and synchronized to the two authorized personal installations. All 40 target SHA-256 values match the public archive; each account's 143 unrelated files were preserved. Both installed default latest checks returned `SKILL_UPDATE_CURRENT 1.1.39`, and both Skill validations passed.

The separate static inventory covers 9 existing systems, 31 modules, 35 pages and 142 Actions. Shared libraries, fixed personal records, NAS-sensitive directories and notification owners are classified separately; nine old multi-scope Actions and one missing-policy Action retain exact-baseline review requirements. This inventory is not evidence that every current server route passed dynamic allow/deny/revoke testing or that existing systems were deployed.
