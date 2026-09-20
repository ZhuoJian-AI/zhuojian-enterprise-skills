# Repository Guide

Mobile navigation preference is a mandatory SaaS-owned interaction: first visit expanded, module selection preserves state, explicit user toggles persist by tenant/user and synchronize same-browser windows. Subsystems provide stable module registration and must not reset platform preferences. Core 1.1.16 records this requirement; publication and deployment evidence belongs in the mobile navigation handoff.

Controlled module-navigation theming was introduced as optional in core 1.1.10 / bundle-v1.4.10. Core 1.1.11 makes the four validated colors mandatory for every subsequent Skill-managed subsystem release; existing SaaS registrations retain a safe default-color fallback. Neither Skill release rewrites or deploys downstream systems. Release evidence is in `docs/handoff/2026-09-17_navigation-theme.md` and the 2026-09-18 required-theme handoff.

Mobile module grid / truthful leave-state requirements released in core 1.1.9 / bundle-v1.4.9. Public install and local upgrade verified; no business ECS deployment. See `docs/handoff/2026-09-17_mobile-grid-guard.md`.

Mobile acceptance release: core 1.1.7 / bundle-v1.4.7; evidence and remaining device-test limits in `docs/mobile-acceptance-20260917.md`.

Standard navigation released: core 1.1.8 / bundle-v1.4.8; additive 2.4/2.5 bridge contract, matching SaaS deployed, no downstream deployment. Public install/update verified; status/evidence in `docs/handoff/2026-09-17_standard-navigation.md`.

## Scope

This is the canonical public monorepo for ZhuoJian enterprise Codex Skills. One Skill remains one self-contained folder with its own `SKILL.md`, `skill-version.json`, and `CHANGELOG.md`. Company-specific behavior must not be copied into the core Skill.

## Workflow

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
