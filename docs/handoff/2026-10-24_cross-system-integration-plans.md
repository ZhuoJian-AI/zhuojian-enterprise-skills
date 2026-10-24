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

Result: **58 passed in 0.12s**. The subsequent approval URL `section/tab` compatibility adjustment has an extra parametrized case and needs a focused rerun. Full core pytest and quick validation are pending; root agent coordinates complete candidate validation and publication.

## Remaining release boundaries

This is a source candidate. Push, reviewed merge, full package verification, immutable Release, anonymous installation/updater checks and both account synchronization have not been performed by this subtask. The platform capability must be independently implemented, tested and published; Skill publication alone cannot activate the plan API or claim a specific enterprise integration is complete. No downstream 2.4/2.5 migration or unrelated application rollout is required.
