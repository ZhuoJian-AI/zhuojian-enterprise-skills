# Business AI Acceptance Candidate

**Publication update:** core 1.1.29 / bundle-v1.4.30 was subsequently published from PR #60 merged source `a7caac9b299f27573156990711e2c5c2d1464c20` at 2026-10-01 22:32:29 CST. Public asset hashes, original-updater fresh/local installation and CURRENT checks passed. The sections below preserve the earlier candidate checkpoint; current evidence is in [the stable release handoff](2026-10-01_business-ai-acceptance-release.md). No runtime deployment or employee-business acceptance is implied.

## Scope And Status

- Skill owns this reusable development and acceptance guidance. SaaS owns public assistant orchestration, completion, persistence/streaming, source context, artifacts, permissions and shared loading; each subsystem owns its business facts, relationships, state semantics and initialization.
- Dedicated branch `codex/ai-business-acceptance-20261001`, baseline `c5428c05dbdc1d86630823e95588914a1b2c411c`, claim `49d190c`. Version/release metadata is single-flight under this task.
- Core candidate version is 1.1.29; proposed next stable bundle is `bundle-v1.4.30`. Supported contract revisions remain 2.4/2.5 and the new-project default remains 2.5. Schema, runtime templates, updater, release builder, catalog selectors and the other four Skills are unchanged.
- No source push, PR merge, tag, Release, workstation Skill installation or SaaS/subsystem deployment is performed by this candidate task. Installed stable Skill stays 1.1.28 until the prescribed post-publication update.

## Changed Guidance

- `SKILL.md` routes affected assistant/file/context/data/loading repairs directly to incremental acceptance without requiring a new full interview.
- `references/business-ai-delivery.md` distinguishes observed business completion from successful auxiliary steps, persisted answer truncation from only streaming failure, current source context from stale callbacks, and real source file versions from metadata-only evidence.
- Seven conditional acceptance groups cover completion/recovery, output/streaming, home/sidebar context, file delivery/reading, relationship/attachment facts, historical data/reasoning/DLP and cold/warm loading with revocation. No fixed business answers or mandatory tool trajectory is introduced.
- Unknown source timestamps remain unknown. A genuine business relationship error is not recategorized as identity/SSO corruption without evidence. Aggregated state is not per-file confirmation; historical samples are not realtime data; a limited employee catalog is not the enterprise's complete deployment inventory.
- File storage/download support is distinct from AI parsing limits and content coverage. Real bytes, version, format and integrity evidence are required where applicable; original bytes not acquired cannot be called corrupt. Partial text extraction cannot imply image/media understanding. No global limit increase, false receipt, DLP disablement, permission bypass or successful-write replay is allowed.
- Loading measurement distinguishes entry click, login, iframe readiness, real first-screen business data and assistant availability. Cache optimization must not expose business-seeded HTML/private APIs anonymously or retain obsolete authorization; current revocation remains effective.
- Existing `docs/ai-delivery.json` schema is unchanged. Its validator checks only structural/declared evidence consistency and cannot prove original bytes, real business semantics, deployed performance, coverage or revocation tests.

## Tests

Commands were run serially, with existing local dependencies and synthetic fixtures, not a real enterprise database:

```text
cd skills/core/zhuojian-subsystem-builder
python -m pytest tests/test_ai_delivery.py -q
python -m pytest -q -ra
python <skill-creator>/scripts/quick_validate.py .
git diff --check
```

- Focused acceptance: 32 passed in Python 3.12 (89 subtests). Two new behavioral tests ensure an earlier successful auxiliary case cannot hide a failed/unrun/evidence-free final delivery and an unavailable original remains blocked even when metadata query passed.
- Python 3.10.11, matching the repository CI major/minor: **522 passed / 53 skipped** in 28.60 seconds. Skips are 3 POSIX ownership/mode cases and 50 route tests that execute only in a generated template project; do not count them as tested by collection alone.
- An earlier Python 3.12.14 full run passed 521 / skipped 54 (124 subtests), with one extra browser prerequisite skip. Final release-candidate count above uses the complete Python 3.10 run; it does not silently combine two environments.
- First version-bumped full run caught the existing test's pinned old version; its expected Skill version was updated to 1.1.29 while contract assertions stayed 2.4/2.5. Final serial reruns passed.
- `quick_validate`: Skill is valid. `git diff --check`: passed.
- Packaging smoke verification uses the existing deterministic package helper plus original updater extraction/candidate validation against an isolated temporary destination. This is an offline candidate archive, not a stable Release or public-install proof. Packaging evidence is appended after execution below.

## Offline Candidate Package Evidence

- Clean candidate source `d9cf68a43466b03dfe353954a1a703b0562679c8`. `package_skill` only: all five ZIP CRC checks, archive SHA-256 and every packaged tracked file byte comparison passed. No formal builder entrypoint, stable catalog, remote write or installation replacement was used.
- Core archive: 1.1.29, 156 tracked files, 604,580 bytes, SHA-256 `7130a897c988933ba0a8342f5b86af720eb3d4eec983a2ee1183ccd73fb040dc`. Original updater `safe_extract` and `verify_candidate(..., "1.1.29")` passed in a temporary directory, which was removed afterwards.
- Source differences against the baseline are empty for the other four Skills, catalog and release builder. Their smoke ZIP hashes: legacy `4cc7c708d5357a6626d322cd3b3d4a5212b2f5c02db30dbcf2715ce25f0f3940`; SQL handoff `0a8667a8e34251f5468fe9f7d3f43f8b3c96a16895198ab3c46a4aafe23ec37f`; goods handoff `5fb6f81cd82b14f35893f5d99843af670fe4a2738cb53f308883e095d995c62f`; NAS handoff `7a78812f1ad72efb517b9ad484f7b10e7ec6a209c5f45bbc784f460bf645192e`. These are local candidate bytes, not a verified public Release comparison.
- All 42 local links in the edited entry/reference resolve; incremental acceptance anchor discovery passed.
- One initial standalone packaging harness missed registering a dynamically imported dataclass module; the harness was corrected and the complete checks reran successfully. No release/updater source changed for that harness error.

## Publication And Remaining Work

1. Independent review and PR/main CI, then merge the scoped branch. Update the organization's wiki milestone card through the authorized workflow.
2. Build all formal assets from clean merged `main` using `scripts/build_release.py --tag bundle-v1.4.30 --output-dir <outside-repository-artifacts>`; do not publish feature-branch smoke assets.
3. Verify all nine public anonymous assets/hashes, original-updater fresh install/CURRENT and local upgrade/CURRENT. Compare the four unchanged Skill ZIPs and exact installed files.
4. Only after stable publication update the installed core via its prescribed updater and reload the new changelog/SKILL/reference; do not copy development files into installation.
5. SaaS and subsystem changes require their own code/build/deployment and real user-flow checks. This Skill publication will not repair existing assistant bugs, source data, file parsing or loading by itself. Any unavailable original, permission, unmeasured case or unresolved dependency stays open and is not marked business-verified.
