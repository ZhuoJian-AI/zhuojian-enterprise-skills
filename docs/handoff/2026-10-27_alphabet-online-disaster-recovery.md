# Alphabet online recovery implementation

Status: candidate code and local fixture verification only. No production installation,
service switch, new backup, cloud upload, or fresh business restore is claimed here.
Root owns the common Skill documentation/version release and dedicated enterprise
backup identity. This branch owns the Runtime helpers and Alphabet compatibility patch.

## Evidence and scope

Fresh metadata observation at 2026-10-27 22:44–23:10 CST verified the existing
`aifabei-hk-01` identity and nine healthy applications. Three legacy applications
keep their actual SQLite databases at container `/app/subsystem.db`, outside the
existing `/data` archive. New online plans explicitly record those original targets.
Seven apps use the existing `apps/` namespace; two continue local-managed storage.
The existing Windows offsite chain remains limited to its original two applications.

`runtime_online_backup.py` uses the SQLite online-backup API, full file hashes,
bounded metadata reference checks, and fixed application-prefix OSS list/head/get.
It captures current committed Git refs, release/env/storage configuration, reviewed
same-enterprise host identity/registry files, original DB targets, and container
image/mount/network layout. Source release/container changes reject the point;
business services are never stopped or imported. Per-database consistency is not
claimed to be a cross-database atomic snapshot.

Schema 3 explicitly sets `consistentOfflineSnapshot=false`. Its private embedded
manifest is hashed, uploaded using the existing enterprise-scoped transport, bound
to an exact object version and fully read back. Isolated restore verifies the
manifest member set, every file hash, SQLite integrity/foreign keys, Git commits,
file references and configuration identity. It never starts the restored app or
executes external business actions. Safe UI restore status remains partial until
a separately controlled service reconstruction is tested. Image bytes and external
NAS/Daoxun originals are explicitly excluded.

`runtime_recovery_evidence.py` observes only existing local receipts, never archive
or object bodies, DB rows, Docker, cloud clients, backup or restore. Its fixed CLI
will publish safe metadata to `/var/lib/zhuojian-operations/recovery-points-source.json`.
Original capture/upload/readback/restore times remain original; fresh observation
does not invent a new recovery point. Latest job failure preserves prior points.

## Rollout gate and compatibility

Install helpers into a new content-addressed directory only after code review and
tests. Unknown wrappers and source paths are not overwritten. Configure only the
pre-authorized same-enterprise backup identity; do not change source bucket rights.
Run namespace/version/private-object probes and full restore per application,
sequentially, preserving at least 5 GiB for production.

Only after all nine new points have exact-version offsite/readback/isolated proofs
may the existing daily timer's ExecStart be changed by a narrow drop-in. Do not call
the old backup routine, which stops applications. The reviewed maintenance patch
accepts schema 3 in the existing Windows gate/exporter without forging the offline
flag or changing the two-app/eight-file/ACK/retention contract. Runtime and cloud
changes require separate actual receipts; none are implied by this source commit.

## Verification

Local targeted suite: 60 passed, 1 skipped (platform-specific existing transport test).
Tests include a live WAL snapshot with continued writes, FK failures, missing and
corrupt references, traversal rejection, source mutation detection, actual Git
bundle and schema-3 upload/readback/isolated restore, metadata-only observation,
failed-latest/prior-point retention, wrapper preservation and Windows compatibility.
Full Linux CI and actual enterprise rollout/restore are pending.
