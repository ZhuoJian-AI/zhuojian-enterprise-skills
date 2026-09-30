# Repository Guide

Core 1.1.28 / bundle-v1.4.29 was published at 2026-09-30 21:09:34 CST from clean merged source `f95ce12e` (PR #58). Complete business-entry identity acceptance, actor/target/eligibility boundaries, native-template HTTP regressions and explicit pending pre-registration results preserve 2.4/2.5. PR/main CI, 520 passed / 53 skipped, nine anonymous asset hashes, original-updater fresh/local install and CURRENT, and 156-file comparisons passed. This does not deploy or certify existing systems. See `docs/handoff/2026-09-30_2110_identity-acceptance-release.md`.

Core 1.1.27 / bundle-v1.4.28 was published on 2026-09-30 at 20:06:12 CST from clean merged source `d9c09aac` (PR #56), after the separate SaaS release. Optional employee-directory Action declarations, Runtime capability projection and native-template search/resolve helpers preserve 2.4/2.5 and ordinary no-directory SSO/Actions. Merged-source 501 passed / 46 skipped, all nine anonymous asset hashes, original-updater fresh install/CURRENT and local upgrade/CURRENT passed; the other four Skill ZIPs are unchanged. Five downstream owners were notified without a forced deployment or protocol migration. Historical repair guidance covers all references and preserves scores/snapshots. See `docs/handoff/2026-09-30_2010_trusted-directory-release.md`; Skill publication does not install Runtime helpers or repair business data.

Core 1.1.26 / bundle-v1.4.27 was published on 2026-09-30 from clean merged source `032a7d1` (PR #54). Optional display names cannot gate authorized personal operations; verified roster repairs require explicit identity evidence, backups and guarded transactions. All nine anonymous assets, original-updater fresh install/CURRENT and local upgrade/CURRENT passed. The other four Skill ZIPs are unchanged from 1.4.26. This contract publication is separate from runtime deployment; see `docs/handoff/2026-09-30_optional-display-identity.md`.

Current company handoffs SQL 1.1.2 / goods 1.0.2 / NAS 1.0.3 were published in bundle-v1.4.26 from clean merged source `6bfab6d8c355aa27aaccc34fd813b71a636cf125` (PR #52) at 2026-09-29 14:32:15 CST. All nine anonymous assets, original updater fresh install/CURRENT, local managed upgrades/CURRENT, exact Runtime resolution and all installed-file comparisons passed. Core 1.1.25 and legacy 1.2.0 ZIPs are byte-identical to bundle-v1.4.25. The deployment stub fetched current rules `fa8415f` with STUB_OK=1. See the final closure handoff for evidence; the next paragraph preserves the prior release and preparation checkpoint.

Core 1.1.25 / bundle-v1.4.25 was published from clean merged source `af6f004` (PR #50) on 2026-09-29 at 01:38:21 CST. It adds guarded regional migration and refreshes company handoffs for the active Hangzhou hosts while retaining stable Runtime identities. All nine anonymous assets, original-updater fresh install/CURRENT, this workstation's core and three managed-company updates, precise new-host resolution and installed-file comparisons passed. The legacy compatibility ZIP is unchanged. Runtime, DNS and employee SSO have separate deployment evidence. On 2026-09-29 the company LAN clients changed to direct Hangzhou tunnels with real HTTP/SQL/SMB reads; restricted Hong Kong relay units and dedicated grants were removed at 13:32:21 CST. The existing mobile overflow and public reminder 429 remain separate issues. Main-host OSS backup credentials and the full daily service with exact-version readback passed at 12:19:51 CST. These facts supersede earlier pending checkpoints. Company patch versions SQL 1.1.2 / goods 1.0.2 / NAS 1.0.3 prepare bundle-v1.4.26; core 1.1.25 and legacy 1.2.0 remain byte-identical. See `docs/handoff/2026-09-29_mainland-final-closure.md` for publication and remaining boundaries; do not infer a Release from a source merge.

Core 1.1.24 / bundle-v1.4.24 was published from clean merged source `1ec53d1` (PR #45) on 2026-09-27. Desktop and mobile retain distinct interactions but each must continuously adapt within the available container; background coverage, content width, long content, clipping, operation reachability and state preservation have separate acceptance checks. PR/main CI, 458 local tests (41 skipped), all nine public asset hashes, anonymous fresh install/CURRENT and this workstation's 1.1.23 upgrade passed. The four unchanged Skill ZIPs retain their hashes. This is a Skill contract release; it does not rebuild or deploy SaaS or existing subsystems. See `docs/handoff/2026-09-27_continuous-responsive-contract.md` for scope and untested real-device limits.

Core 1.1.20 / bundle-v1.4.20 was published from merged source `f429ee1` (PR #37), after SaaS source `9f104d5` / manifest `3cbe964` completed protected deployment at 2026-09-22 21:39:17 CST. The four validated navigation-theme colors may coordinate the current application's SaaS navigation rail, common controls and unified-assistant entry without styling other applications, assistant content or the business iframe; switching and leaving must replace or clear the scoped variables. All nine Release asset hashes match, public fresh install/CURRENT/1.1.19 upgrade passed through the original updater with a temporary curl transport, and this workstation is on 1.1.20. Existing correctly registered subsystems were not rebuilt or deployed. Evidence is in `docs/handoff/2026-09-22_adaptive-shell-theme-contract.md`.

Mobile navigation preference is a mandatory SaaS-owned interaction: first visit expanded, module selection preserves state, explicit user toggles persist by tenant/user and synchronize same-browser windows. Subsystems provide stable module registration and must not reset platform preferences. Core 1.1.16 records this requirement; publication and deployment evidence belongs in the mobile navigation handoff.

Controlled module-navigation theming was introduced as optional in core 1.1.10 / bundle-v1.4.10. Core 1.1.11 makes the four validated colors mandatory for every subsequent Skill-managed subsystem release; existing SaaS registrations retain a safe default-color fallback. Neither Skill release rewrites or deploys downstream systems. Release evidence is in `docs/handoff/2026-09-17_navigation-theme.md` and the 2026-09-18 required-theme handoff.

Mobile module grid / truthful leave-state requirements released in core 1.1.9 / bundle-v1.4.9. Public install and local upgrade verified; no business ECS deployment. See `docs/handoff/2026-09-17_mobile-grid-guard.md`.

Mobile acceptance release: core 1.1.7 / bundle-v1.4.7; evidence and remaining device-test limits in `docs/mobile-acceptance-20260917.md`.

Standard navigation released: core 1.1.8 / bundle-v1.4.8; additive 2.4/2.5 bridge contract, matching SaaS deployed, no downstream deployment. Public install/update verified; status/evidence in `docs/handoff/2026-09-17_standard-navigation.md`.

## Scope

This is the canonical public monorepo for ZhuoJian enterprise Codex Skills. One Skill remains one self-contained folder with its own `SKILL.md`, `skill-version.json`, and `CHANGELOG.md`. Company-specific behavior must not be copied into the core Skill.

The `assistant-open.v1` contract hands a business goal to the same SaaS assistant as a source-bound draft, never an automatic Run or approval. Runtime capability discovery describes backend implementation only; browser negotiation and current employee authorization remain separate. Business data and Actions stay on subsystem servers. Early candidate evidence: `docs/handoff/2026-09-22_assistant-entry-bridge.md`; current release status is recorded in the workflow handoff below.

The optional `assistant-suggestions.v1` contract reports bounded snapshots of genuine checks on the currently authorized page. SaaS owns non-modal presentation and employee preflight; choosing a suggestion still only imports a draft into the same assistant. No employee surveillance, automatic send, background Run, or additional model identity is introduced. Deduplication is scoped to a continuous source session, not permanent cross-session memory. Templates and acceptance rules are in `references/assistant-page-suggestions.md` inside the core Skill; earlier local evidence is in `docs/handoff/2026-09-22_1519_page-suggestions-skill.md`.

## Workflow

The optional workflow-guidance contract supplies bounded business descriptions and explicitly enabled foreground read checks, not a second agent or background delegation. Active SaaS must advertise `assistantWorkflowGuidance` before downstream declaration. `workflowGuides` is permission-filtered reference material; `proactiveCheck` names a genuine side-effect-free employee Action with fixed context input and an explicit result contract. Legacy 2.4/2.5 stays compatible.

Core 1.1.19 / bundle-v1.4.19 was published from merged source `6eba784` (PR #35), after SaaS source `8983e5b` / manifest `aa5a9a7` finished protected deployment at 2026-09-22 19:22:59 CST. All nine public asset hashes match; the four unchanged Skill ZIPs retain their previous hashes. Public fresh install passed with the default updater; old upgrade, legacy migration and this workstation's installation passed through a temporary curl transport retaining original updater integrity/atomic-install checks after intermittent urllib failures. This is not proof of business subsystem or Runtime helper deployment. Current evidence and remaining real-flow/device acceptance are in `docs/handoff/2026-09-22_1657_assistant-workflow-guidance-skill.md`.

- Milestone merges must update `zhuojian-llm-wiki/cards/zhuojian-enterprise-skills.md`; Skill publication is separate from SaaS or subsystem deployment.
- Work on a `codex/<description>` branch and merge through a reviewed pull request.
- Never put passwords, SSH private keys, database credentials, tokens, customer data, or local access profiles in Git or Release assets.
- Stable updates come only from immutable GitHub Releases. `main` is source, not an update channel.
- Keep `catalog.json` selectors narrow. Server-specific Skills need a `runtimeIds` or `hosts` selector; an enterprise-only selector is reserved for rules that truly apply to every server of that company.
- Run the affected Skill tests and quick validation before merging.
- Build a Release only from a clean merged `main` commit.

## Commands

```text
cd skills/core/zhuojian-subsystem-builder && python -m pytest -q
cd skills/core/aifabei-subsystem-builder && python -m pytest -q
python C:/Users/王鑫涛/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/core/zhuojian-subsystem-builder
python C:/Users/王鑫涛/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/core/aifabei-subsystem-builder
python scripts/build_release.py --tag <bundle-tag> --output-dir <temporary-directory>
```

Run canonical core tests from `skills/core/zhuojian-subsystem-builder`. When compatibility behavior changes, also run the focused updater tests in `skills/core/aifabei-subsystem-builder`. Validate every changed Skill directory separately.
