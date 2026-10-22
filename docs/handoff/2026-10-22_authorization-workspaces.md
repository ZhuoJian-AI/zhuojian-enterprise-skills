# Fixed workspace business authorization

Scope: the Builder Skill owns declarations, starter behavior and acceptance requirements. SaaS owns persisted role workspaces, active departments, exact resource grants and revocation. Business systems own real record departments and their REST/import/export services. This change does not register a Manifest, modify roles, migrate customer records or deploy a service.

Base: `8823c625a67047a72c5b1e8bd90274d97b613a40`; dedicated branch `codex/authorization-workareas-contract-20261022`. Core version advances from 1.1.38 to 1.1.39; integration revisions remain 2.4/2.5. The former main checkout is unchanged.

## Contract and behavior

- Explicit `permissionPolicy={group:management,mode:workspaces}` has no supportedScopes or scopeLabels. The existing effectiveDataScope wire remains a set of live same-enterprise department IDs with all broad/self flags false, including for the managed developer role.
- Employee D0 is default. For each exact application/module/page/Action, only its independently granting active roles contribute D0 plus their added departments. No Action means no business permission; no department means no fallback to all. Workspace and module configuration remain independent.
- Existing configurable, fixed personal and public policies retain their meaning. Do not infer a conversion from CRUD, record creation department, a file location or labels. Shared libraries, NAS-sensitive directories and notification owners retain dedicated boundaries.
- Scaffold adds the explicit `department-workspaces` model. New records default to D0 or use a department in the Action's current allowed list. Existing records keep their department after the employee moves, and ordinary update cannot reassign them. Unexpected broad/self scope is rejected for the fixed mode.
- Resource-specific routes can set `expected_context` on the shared file-action guard. A valid Action from another resource fails before live checking or accessing business data. Generic file routes continue binding every query to the authorized module.
- Import preview and commit must distinguish create and update scopes, recheck at commit, check versions and roll back a mixed unauthorized batch. The generic scaffold has no import endpoint; the Skill does not claim its documentation implemented each downstream importer.
- Technical preflight emits six authorization checks as pending. Health, a synthetic JWT, Manifest fields or a declared success cannot turn them into real employee authorization evidence.

## Validation

Commands use the existing isolated validation Python environment, with no production database or customer HTTP requests:

```text
python -m pytest -q tests/test_permission_policy.py tests/test_checkbox_permissions.py tests/test_authorization_acceptance_report.py tests/test_generated_native_template.py tests/test_acceptance_identity_report.py
97 passed

python -m pytest -q
607 passed, 56 skipped, 1 existing anyio deprecation warning

python <skill-creator>/scripts/quick_validate.py skills/core/zhuojian-subsystem-builder
Skill is valid!

git diff --check
passed
```

The generated-project test runs the copied starter's actual route/security/recovery suite against temporary SQLite and file storage; it includes fixed resource mismatch, malformed scope, stable record departments and out-of-scope negative cases. Conditional tests skipped by the upstream suite are not evidence of real server/browser/device acceptance. Current production sessions, actual employee data, mobile devices and every downstream route remain separate integration verification.

## Publishing and synchronization

This is a local implementation candidate. Before registering any `workspaces` policy, publish and verify every SaaS consumer (including workers) can read it. Rollback restores downstream old Manifest endpoints and officially registered metadata first, then old consumers; preserve explicit denials and real grants. Build the stable bundle only from the eventual clean merged main, never relabel this feature commit as a stable release.

The two installed personal Skill copies are compared to the exact base for only this task's changed files. Back up those files, preserve unrelated files and reject conflicts; verify byte hashes after copying. Per-account evidence and candidate package receipts live outside Git. Existing subsystem inventory is static evidence with per-Action migration status; it is not a server-deployment receipt.
