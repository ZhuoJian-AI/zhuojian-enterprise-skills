# Repository Guide

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
