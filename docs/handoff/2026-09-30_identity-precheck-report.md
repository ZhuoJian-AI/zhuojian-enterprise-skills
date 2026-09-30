# Identity Precheck Report Boundary

## Scope

Skill-only candidate from `f763b849aa19bb1210937861c40392206616fc8d`, rules `fa8415fc48cf9291f3c4030b69f78c33cc291a88`. Changes are limited to `scripts/e2e_acceptance.py` and its focused tests. The coordinator owns version metadata, the reference contract, full-suite verification and publication. No business ECS, Runtime release chain, SaaS schema, credential or employee permission was changed.

## Behavior

- Preserve `status=pre_registration_only` and the existing technical query/SSO results. `realSso` now stays `pending_admin_acceptance` for both 2.4 and 2.5; acceptance of a locally signed 2.4 ticket is still reported in `sso`, not promoted to real employee SSO.
- Add `identity_acceptance_pass=null` and `identity_results` using the existing pending-result shape (`passed=null`, `failures`). These are unanswered checks, not executable evidence or a new deployment gate.
- Legacy HTTP/local authentication and the affected flow's identity relationships remain unverified because a Manifest cannot enumerate them. Distinguish actors, selected employees and external contacts; do not require full historical migration for ordinary changes.
- Generate personal isolation checks only for declared self/self-capable Actions. Only their write operations receive the no-display-name browser-form check, with legitimate business participation conditions preserved.
- Generate trusted selection checks only for explicit `employeeDirectory:true`, associated with the declaring module/Action and its actual pages. Names, CRUD operation names, healthy status and caller-supplied acceptance fields cannot turn these items into a pass.
- No new HTTP calls, CLI input for manual evidence, authentication behavior, schema fields or runtime mutations were added.

## Focused Verification

From `skills/core/zhuojian-subsystem-builder`:

```text
python -m pytest tests/test_acceptance_query_probe.py tests/test_acceptance_identity_report.py -q
```

Result: **34 passed** (15 existing denial checks, 19 new report/CLI checks). The four 2.4/2.5 success/denial CLI combinations execute `main` with the existing real semantic validator and stubbed HTTP/runtime credentials. They verify unchanged request count and query-only business calls, pending real identity/SSO results, preserved technical outcomes and no printed secrets. Pure-function cases cover declaration-based applicability, module/page binding, input immutability, absent/false directory flags and rejection of supplied success metadata as evidence.

These tests verify the report's truthfulness, not any employee browser, old HTTP route or business identity implementation. Full tests and stable publication are left to the coordinator; no production deployment was performed.
