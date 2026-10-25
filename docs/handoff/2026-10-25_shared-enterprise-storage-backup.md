# Shared enterprise storage and recoverable off-server backups

Owner: `fix_storage_inventory`. Base `5d6ffe6`; isolated branch `codex/multi-owner-storage-20261025`. Runtime helper, main Skill/version/CHANGELOG, SaaS and production rollout are coordinated by the root task.

## Implemented

- New gateways derive `enterprises/<organization UUID>/<environment>/apps` from the private Runtime profile. Legacy objectStorage profiles without a namespace keep `apps`. Installer validates trusted identity before replacement; probes verify exact expected prefix and cross-enterprise/backup denial. The existing registry stores application slugs/state/token hashes; full object keys are derived, not persisted in each registry row.
- Independent `zhuojian-backup-oss` CLI: one-time configure/probe, v2 consistency archive publication, exact OSS version and whole-object SHA verification, anonymous-read denial, remote manifest discovery, isolated Git-bundle restore verification, and optional bounded local retention. Multipart tests exercise a 513 MiB archive with at most 8 MiB buffers.
- Backup identity is separate from business attachments, scoped to one enterprise/environment in a shared backup bucket. No cloud deletion capability is needed. Unknown multipart initialization does not acquire bucket-wide ListMultipartUploads permission or blindly retry the write.
- Root-only versioned installer and opt-in existing-backup-unit drop-in; no automatic configuration, timer enablement, migration or upload during installation. Enterprise trusted root development remains supported.
- Updated object-storage/admin-bootstrap docs and added runtime-backup-recovery instructions for future Codex discovery and verification, including the legacy bucket migration boundary.

## Tests executed locally

Using the existing skill-test-venv Python on Windows:

```text
python -m pytest -q tests/test_runtime_backup_oss.py tests/test_install_runtime_backup.py
23 passed

# Gateway directory; PYTHONPATH must point at this worktree's gateway/src.
python -m pytest -o addopts= -q tests
45 passed, 2 skipped, 1 existing anyio deprecation warning
```

Tests cover namespace isolation in actual HTTP handlers, >512 MiB multipart processing, exact object versions, malformed and corrupt evidence, unknown-write readback, bounded retention preserving unverified recovery points, real Git bundle/clone recovery, unsafe archive members, cross-enterprise credential probes, profile-write failure, and installer failure preserving the previous wrapper. Windows skips are not Linux passes; root will coordinate combined Linux/core/legacy/systemd validation after integration.

## Live read-only evidence and rollout boundary

Local sanitized audit artifacts live under `audit-2026-10-25/multi-owner-self-service-fix/storage/` in the SaaS workspace, outside this distribution repository. As inspected on 2026-10-25:

- Alphabet 47.97.90.161 still uses private bucket `alphabet-prod-hz-files-20260928` with `apps/`; it has not been moved to shared buckets.
- Nine managed Git repositories were clean; only five had a remote configured, which is not proof of pushed history.
- Latest local backup service succeeded, but the inspected helper/unit had no OSS upload or retention. Existing archives omitted Git. Backup directory was about 5.10 GiB; latest nine archives total 1,857,140,110 bytes, with inspiration alone 1,777,235,213 bytes.
- No production files, credentials, cloud objects, RAM policies, buckets, timers or data were changed by this storage task. The old 101 host was not accessed.

Deployment requires authorized one-time shared bucket/RAM initialization, updating host/gateway tools, actual publication and isolated restore, then enabling the drop-in. Existing business objects need a separate copied-and-verified migration with coordinated profile/credentials/release switching and preserved registry identities. Skill package changes alone do not prove any of those live steps.
