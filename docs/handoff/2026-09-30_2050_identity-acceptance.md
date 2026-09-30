# Complete Business Identity Acceptance

Owner/task: Codex / IDENTITY-ACCEPTANCE-20260930. Rule source: `fa8415fc48cf9291f3c4030b69f78c33cc291a88`, freshly fetched with STUB_OK at 20:45 CST. This is a Skill-only change; source merge, stable publication and downstream deployment are separate states.

## Scope

Core candidate 1.1.28 retains integration 2.4/2.5. The new `references/identity-acceptance.md` makes actual business-entry inventory, trusted actors versus selected employees, legitimate eligibility and business-level acceptance explicit. Reachable legacy HTTP paths and local authentication cannot bypass SaaS authorization; isolated operations/machine protocols and harmless static shells keep their own documented boundaries. Browser live checks and short-lived platform Action JWT validation are not conflated.

Employee-directory guidance now explicitly exempts authorized self-enrollment from selecting oneself, without allowing historical name claims. External contacts remain business data. Historical inventory distinguishes active identity relations, immutable receipts and display snapshots; it must not blindly replace every old ID string. Existing deployed capabilities and published contracts are reused rather than republished for every business fix.

The pre-registration CLI adds pending identity results and leaves real employee SSO pending for both supported revisions. It does not add network requests, mutate business data or accept manually supplied checklists as evidence. See `2026-09-30_identity-precheck-report.md` for its exact boundary.

Only native-template tests changed, not its runtime implementation. The new HTTP regressions exercise generated source, real ASGI routes/session middleware/local validation and temporary SQLite. Remote SaaS exchange/session-check transport is simulated. Business APIs reject absent/expired/revoked identities and transport failures; authorized nameless employees can write/read their own records; client identity fields cannot replace authoritative ownership; same-name identities remain separate. Machine Actions separately cover valid trusted ownership and invalid/expired credentials, not a claimed live SaaS revocation end-to-end result.

## Verification Before PR

- Canonical core: `python -m pytest -q -ra`: **520 passed, 53 skipped in 24.65s**. The generated-template test invokes the generated project's suite. Raw unrendered template tests intentionally skip; three POSIX ownership/mode checks skip on Windows. Skips are not passes.
- Independently generated project: `python -m pytest tests/test_action_routes.py -q`: **31 passed**, including seven new HTTP identity cases with parametrized route matrices and database no-side-effect checks. Six pre-existing FastAPI lifecycle deprecation warnings remain.
- Precheck-focused: `python -m pytest tests/test_acceptance_query_probe.py tests/test_acceptance_identity_report.py -q`: **34 passed**, including four 2.4/2.5 success/denial CLI combinations.
- `quick_validate.py skills/core/zhuojian-subsystem-builder`: valid. `git diff --check`: clean.
- Independent forward test used a volunteer subsystem with a legacy password route, employee/external contacts, self-enrollment, identical names and immutable receipts. It rejected premature deployment and retained legitimate participation/external contacts. Its two actionable scope findings (self-enrollment and reusable capability dependency order) were incorporated. This is decision-quality evidence, not a deployed application test.

## Publication And Downstream Boundary

At this source checkpoint the stable package is not yet published; public install and local update remain pending. Build only from clean reviewed merged main after PR/main CI, publish core 1.1.28 in bundle-v1.4.29, compare all nine assets, then run anonymous original-updater fresh install/CURRENT and local upgrade/CURRENT. Record exact source, hashes and results in a subsequent release receipt rather than editing immutable assets.

SaaS owns canonical identity/current authorization/directory. Skill owns this contract, template and truthful precheck. Subsystems own actual route enforcement, business relationships, forms and historical repairs. No SaaS, Runtime helper, business repository, server, role, password or production record is changed by this task.

Recorded consumers: coa (ZhuoJian integration surface only; independent toC unchanged), garment-production-collaboration, chairco-product-library, aifabei-sample-review and aifabei-production-handoff. Notify applicable owners and wiki after publication; historical 2.3 consumers require separate compatibility review, not a version-number edit or automatic template replacement. Correctly implemented consumers need no forced deployment. Identified downstream defects require their own authorized repair and tests; this release does not mark them fixed or certify unaudited systems.
