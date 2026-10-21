# Business-capability checkbox authorization

## Ownership and candidate

- Core Skill candidate: 1.1.37, based on merged main `4f98348bb1b8a38fad30d01c12c85fe1bd5e1eb7` (bundle-v1.4.37).
- SaaS owns the administrator checkbox interface, saving each Action's exact scope, role union, and current employee authorization. Subsystems own the actual record rules. This Skill defines generation, validation, migration, and acceptance.
- No new permission modes; contract 2.4/2.5 revisions remain unchanged. Optional permissionPolicy.scopeLabels presentation metadata requires complete business capability names for each supported scope; identical labels require verified identical effects and preserve existing scope values; it never participates in execution. No business database, employee role, Runtime installation, or SaaS service is modified by this source change.

## Result

Administrators select business capabilities whose names and descriptions identify what can be done and to which business objects. New capabilities have an implemented permissionPolicy; management supportedScopes contains exactly one scope. The interface must not expose a generic self/department/all picker or inherit an unrelated role default. Created-by and assigned-owner rules must be distinguished.

The scaffold requires the developer to explicitly select personal-created or enterprise-shared, produces a single supportedScope and business-facing text, and refuses to create files when that decision is missing. Mixed business workflows still require per-Action design; this is a skeleton rather than an automatic business classification.

Source, endpoint, Runtime publisher, and legacy registration all run the checkbox gate. A deployed, reviewed Manifest may be supplied with --permission-baseline. Compatibility is limited to the same application/enterprise (when declared), moduleKey/actionKey, operation and policy group/mode/supportedScopes. Copy edits and scopeLabels do not alter the boundary; new keys or changed policies cannot borrow an old exemption. The command prints legacyUpgradeRequired / PERMISSION UPGRADE REQUIRED and never changes grants. A baseline must be a preserved deployed artifact, with separate desktop/mobile evidence that SaaS presents legacy boundaries as business checkboxes; a candidate is not its own deployment evidence. Legacy multi-scope Actions without complete scopeLabels only allow retaining/removing previous grants, never guessing newly selectable boundaries.

## Verification

- Real Python 3.12 from the bundled runtime; isolated task virtual environment, no global PATH change.
- Installed updater: SKILL_UPDATE_CURRENT 1.1.36. Managed updater: SQL 1.1.2, goods 1.0.2, NAS 1.0.3 all CURRENT; no other Skill was changed.
- Focused pre-integration suite: 132 passed.
- Full canonical core suite after adding scopeLabels: 598 passed, 53 skipped. The skipped cases retain existing POSIX/platform limits or template-only route tests; generated-project route/security tests ran through test_generated_native_template.
- Final permission, metadata, schema and audit regressions after verified equivalent-label handling: 114 passed. Earlier generated-template integration suite: 118 passed.
- quick_validate: Skill is valid. git diff --check passed.
- Meaningful regressions cover old protocol validity vs release rejection, fixed single scopes on both revisions, scoped legacy compatibility, other-app/enterprise baseline rejection, altered/new operation rejection, missing-policy handling, business copy, source CLI gating, and scaffold refusal before file creation.

## Publication boundary

At candidate preparation this has not been merged, released, or installed to either personal account. Stable publication requires reviewed PR checks and a clean merged main, then bundle-v1.4.38 packaging, public asset hash checks, original-updater install/CURRENT verification and scoped two-account synchronization. Runtime/SaaS/Product360 deployment and actual administrator/employee browser checks are tracked by their owning releases, not claimed here.
