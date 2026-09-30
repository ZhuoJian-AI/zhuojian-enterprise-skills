# Trusted Employee Directory Candidate

This file preserves the implementation checkpoint. Stable publication, public-install verification and downstream notification subsequently completed; the current evidence is in [the release handoff](2026-09-30_2010_trusted-directory-release.md).

- Owner/task: Codex / TRUSTED-DIRECTORY-CONTRACT-20260930. Base: fresh `origin/main` at `bce651f`; isolated branch `codex/trusted-directory-contract-20260930`. Rules read: `fa8415fc48cf9291f3c4030b69f78c33cc291a88`.
- Candidate: core 1.1.27, intended next bundle 1.4.28. Existing stable publication remains core 1.1.26 / bundle 1.4.27. No stable build, push, merge, release, Runtime install or business deployment was performed by this task.

## Implementation

SaaS owns trusted employee identity, current authorization and the optional server-to-server employee directory. The aligned API is `/api/v1/subsystem-sso/employees/search` and `/resolve` with a `zjss_` project credential plus the trusted current employee, auth epoch and concrete module/page/Action context. `employeeDirectory: true` is optional on non-public create/update Actions; ordinary Actions and contract 2.4/2.5 remain compatible.

The Skill schema and semantic validator recognize the opt-in. The Runtime capability projector validates `features.employeeDirectory`, including fixed endpoints, the combined client/employee authentication mode and `targetActiveOnly: true`; absent support remains false. A released Skill alone does not update already installed Runtime helpers or establish SaaS availability.

The native template keeps SSO application identity and optional display metadata. Its employee-directory helper uses the fixed SaaS origin, bounded requests, current server-held identity and no redirects/environment proxy. It checks all five response context fields, canonical UUID identity, duplicate/extra/missing resolve members and bounded pagination; the browser search route cannot supply the actor. Business saves must call the same helper with `user_ids` immediately before binding. No generic roster table, directory Action opt-in, frontend picker or automatic business binding is added to every subsystem.

`references/employee-identity.md` separates SaaS identity from local participation/grouping. An affected historical roster/import audit must include every referenced table and legacy string ID, not merely roster foreign keys. Verified conditional transactions preserve scores, dates and historical name/group snapshots; unresolved mappings remain pending. This generic template does not claim to repair actual employee data or implement every downstream business transaction.

## Validation

From `skills/core/zhuojian-subsystem-builder`:

```text
python -m pytest -q tests/test_permission_policy.py tests/test_manifest_schema_versions.py tests/runtime_host/test_platform_capabilities.py tests/test_generated_native_template.py tests/test_contract_versions.py
149 passed in 8.61s

python -m pytest -q
501 passed, 46 skipped in 23.85s
```

The full run includes generating a complete native subsystem and executing its actual FastAPI/SQLite security/recovery tests. Five new template tests cover fixed trusted directory transport, exact response membership/context, invalid/old identity and revoked authorization, real SSO-to-UI-search success/denial, and unnamed personal creation with forged display/user fields retaining the trusted owner. Raw template-directory tests require a generated `subsystem.json`, so those five add to the raw-template skips; their generated-project run passed. These are isolated fixtures, not real employee actions or live platform directory verification.

```text
python C:/Users/王鑫涛/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/core/zhuojian-subsystem-builder
Skill is valid!
git diff --check
passed
```

## Remaining Release Work

The parent task owns SaaS publication and live directory verification, the core stable bundle and public-install checks, and any necessary Runtime helper installation. Culture owns its actual employee picker, binding/exit service, full historical reference transaction and browser acceptance. Existing correctly implemented subsystems without employee selection need no forced upgrade or deployment. Cross-repository notification and wiki publication should describe the optional capability and relevant next-maintenance work, not claim every consumer has already adopted it.
