# Cross-system integration plans: Skill candidate

Date: 2026-10-24, Asia/Shanghai. Skill source baseline: `96f7ccb`; dedicated branch: `codex/cross-app-delegation-20261024`.

## Behavior and ownership

Core Skill 1.1.42 adds a complete, conditional development workflow for two applications or distinct modules of one application. The developer verifies business ownership, implements both real handlers and the final result path, proposes exact routing edges, directs the enterprise administrator to the normal SaaS session, then uses the originating Runtime to apply only the approved configuration. Configuration waiting does not stop independently authorized subsystem implementation.

SaaS owns the plan API, administrator approval, exact route application/revocation and saved target-receipt evidence. The Skill adds documentation, a Python standard-library client and synthetic regression tests; business handlers and source/target readback remain the relevant subsystems' responsibility. This change does not deploy SaaS, update Runtime executables, modify an existing Manifest, or change any enterprise business records or permissions.

## Client guarantees

- Reads only the original Runtime profile and its existing protected root-owned 0600 registration-key reference. No credential command argument, credential export, administrator token, arbitrary API URL, redirect or response-body error logging.
- Supports `catalog`, `propose`, `status`, `apply`, and `verify` against the separately implemented SaaS contract. Proposal uses a stable request ID, exact connected edges, at most two applications, and at most eight edges. The platform produces `spec_digest` and opaque `version`; the client does not manufacture authorization digests.
- Reads a matching request before proposing. Unknown mutating results cause GET reconciliation only; no automatic POST retry. Existing plans, stale versions, revoked/pending decisions, expired configuration authorization, not-ready capabilities and repeated application remain distinct.
- Verifies only saved platform delivery IDs and real target `processed:true` completed receipts with business entity references and positive versions. Transport-only/false/incomplete/unrelated receipts fail. Output remains `business_acknowledged` with `end_to_end_verified:false`; source final result, target authorized readback and applicable content hash comparison remain explicit business acceptance tasks.
- Configuration authorization expires after its approved application window; an already configured business relation is not silently treated as revoked when that window expires. Explicit revocation is separate.

## Validation

Executed locally using the task-specific Windows Python 3.13.16 (not installed globally):

```text
python.exe -m py_compile skills/core/zhuojian-subsystem-builder/scripts/integration_plan.py skills/core/zhuojian-subsystem-builder/tests/test_integration_plan.py
python.exe skills/core/zhuojian-subsystem-builder/scripts/integration_plan.py --help
git diff --check
```

All passed. WSL Python 3.12.3 lacked pytest; this is an environment limitation, not a passing test result. An indexed candidate tree (`32cfd1dd9cd560588127da8aa23c34ecc072bda6`) was then archived without credentials and tested on the authorized isolated company CI image `zj-cross-app-tests:20261024`, with network disabled and source mounted read-only:

```text
python -m pytest -q -p no:cacheprovider tests/test_integration_plan.py
```

Result: **58 passed in 0.12s**. After adding `section/tab` approval URL compatibility, the first full core run reported **3 failed, 661 passed, 58 skipped**: one existing test pinned the previous Skill release version (now updated to 1.1.42); two gateway fixtures inherited a permissive default process umask and failed the existing protected-file check. No gateway code or credential checks were weakened.

The expanded implementation at `687b440c848404a8f594e9c27455298bad1c066f` then passed **676 tests, 58 skipped** with process-local `umask 077`; quick validation printed **Skill is valid!**. Final HTTP interrupted-response sanitization and one regression were added in `0da5c11`. Its full core run was:

```text
docker run --rm --network none -v <candidate>:/skills:ro \
  -w /skills/skills/core/zhuojian-subsystem-builder \
  --entrypoint sh zj-cross-app-tests:20261024 \
  -c 'umask 077; python -m pytest -q -ra -p no:cacheprovider'
```

Result: **677 passed, 58 skipped, 1 dependency deprecation warning in 16.46s**. The skips are 53 template route tests that require a scaffolded project, one responsive test missing Playwright, and four adapter tests requiring Node.js; this suite does not claim those browser/JavaScript paths passed. No production service or business data was contacted.

Windows Python 3.13.16 additionally passed three standard-library-only smoke checks (same-application distinct modules accepted, wildcard event rejected, and `processed:false` receipt rejected), plus compilation and CLI help. These tests do not prove administrator approval, route configuration, source result readback or end-to-end enterprise behavior in production. The root agent coordinates final candidate package checks and publication.

## Remaining release boundaries

This is a source candidate. Push, reviewed merge, full package verification, immutable Release, anonymous installation/updater checks and both account synchronization have not been performed by this subtask. The platform capability must be independently implemented, tested and published; Skill publication alone cannot activate the plan API or claim a specific enterprise integration is complete. No downstream 2.4/2.5 migration or unrelated application rollout is required.
