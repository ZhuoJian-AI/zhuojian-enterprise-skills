# Alphabet online recovery implementation

Status at 2026-10-28 01:10 CST: reviewed Runtime helpers are installed, all nine
applications have new private OSS points with exact-version full readback and
isolated database/Git/file checks. Eight have complete captured file references;
garment has an explicit 220-reference gap. The measured third-generation
capacity/retention gate passed and the independent online timer is enabled.
Root owns the common Skill
release, both-account synchronization, platform API/UI and main-host changes.

## Evidence and scope

Fresh metadata observation at 2026-10-27 22:44–23:10 CST verified the existing
`aifabei-hk-01` identity and nine healthy applications. Three legacy applications
keep their actual SQLite databases at container `/app/subsystem.db`, outside the
existing `/data` archive. New online plans explicitly record those original targets.
Seven apps use the existing `apps/` namespace; two continue local-managed storage.
The existing Windows offsite chain remains limited to its original two applications;
it is an additional copy, not a prerequisite for the nine-system cloud chain.

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
file references re-queried from the restored primary databases and configuration
identity. It never starts the restored app or
executes external business actions. Safe UI restore status remains partial until
a separately controlled service reconstruction is tested. Image bytes and external
NAS/Daoxun originals are explicitly excluded.

`runtime_recovery_evidence.py` observes only existing local receipts, never archive
or object bodies, DB rows, Docker, cloud clients, backup or restore. Its fixed CLI
publishes safe metadata to `/var/lib/zhuojian-operations/recovery-points-source.json`.
Original capture/upload/readback/restore times remain original; fresh observation
does not invent a new recovery point. Latest job failure preserves prior points.

## Rollout gate and compatibility

Install helpers into a new content-addressed directory only after code review and
tests. Unknown wrappers and source paths are not overwritten. Configure only the
pre-authorized same-enterprise backup identity; do not change source bucket rights.
Run namespace/version/private-object probes and full restore per application,
sequentially, preserving at least 5 GiB for production.

The new independent online service/timer may be enabled only after every system
has two verified local v3 points and a third verified point has actually pruned its
older v3 archive. Legacy archives, all remote versions and metadata receipts are
preserved. Each deletion requires fresh full readback of the exact remote version
and matching isolated DB/Git/files/re-queried-reference evidence. At least two
valid local v3 points remain. Unknown/failed history is preserved, never counted
as a successful point. Keep the 5 GiB production free-space floor.

Only the old timer is disabled; its unit/wrappers are retained. Never call or
automatically reactivate its old routine, which stops applications. The new daily
calendar is 03:15 plus up to 15 minutes randomized delay. Windows export runs as
an independent secondary unit, retaining its original clean-repo, inode, SHA and
capacity guards, plus headroom for the next primary capture. Secondary failure
does not block the cloud chain. The Windows reader accepts strictly verified v3
metadata without pretending it was offline; original ACK bytes remain unchanged.
The legacy ACK-prune operation now reports historical preservation and delegates
only new-v3 retention to the cloud chain; it deletes no native archives.

## Actual installation and recovery evidence

Normal registered SSH verified machine identity and kept all nine business
containers healthy with restart count zero throughout observed rollout checks.
The final helper payload was frozen from `5e7a509c063aebdab61732a07b07c4ce3508b1d7`;
its content-addressed installed release is
`a6de832052f14ef3417b0575ed366c8a3c9553a0941eaab716c5e90d627221ab`.
Every wrapper upgrade used original-byte CAS and retained rollback copies; Runtime
profile and reviewed plan were unchanged by helper installation. The protected
plan separately gained the nine actual registered project IDs and garment's
reviewed missing-key baseline/supplement. No business data or source OSS rights
were migrated or changed.

The target is the existing separate `zhuojianai-staging-backups-hz` bucket in
`cn-hangzhou`, under the exact enterprise/environment backup prefix and per-app
archive/manifest paths. The dedicated RAM identity cannot delete remote backups
or access another enterprise. Real private/versioned upload probes included two
multipart parts (8 MiB + 333 bytes) and exact-version full readback. Same-region
off-server storage is not cross-region disaster recovery.

The first nine points completed by 00:32:46 CST. The second complete generation
completed at 00:45:34, leaving 12,564,684,800 free bytes. Culture and inspiration
first archives were 805,684,967 and 1,974,032,390 bytes. Older first-generation
proofs were genuinely re-restored and their DB references re-queried at
00:47–00:50; all nine now have that evidence. The third generation completed at
01:06:03: every application genuinely pruned one older verified v3 archive and
retained two. Inspiration's 522 one-second samples measured minimum free disk
6,333,534,208 bytes and minimum MemAvailable 1,628,909,568 bytes; post-run disk
was 12,519,100,416 bytes. No free-space floor or archive-lifecycle optimization
was needed. This verifies sustainability for the measured data size, not unlimited
future business growth; future capacity failures preserve existing points.

At 01:08:41, exact local SHA/size/remote/restore/prune gates reported two verified
local points and one verified pruned point for each of the nine systems.
`systemd-analyze verify` and the installed preflight passed. Only the old timer
was disabled; the new timer is enabled, active and waiting, with first natural
next run 2026-10-28 03:22:52 CST. Its LastTrigger is empty: the three manual
verification generations are not falsely described as natural timer execution.
Preflight pins both wrappers and all installed module bytes, plus the protected
plan. CPU/IO weights, nice and idle IO reduce backup priority; no arbitrary
memory hard limit was imposed. A final 01:10 readback verified all nine exact
container IDs unchanged since the switch precheck, healthy with zero restarts,
and the original Runtime admin helper SHA unchanged.

Garment's original source already lacked 275 referenced attachments. The reviewed
baseline permits only those exact key hashes (or a subset), never new missing
references. Main-host historical backups supplied 55 exact SHA-256/size matches
(32,464,688 bytes), relayed only into private backup staging and included in the
new point. The live source remains unchanged. The remaining 220 references are
recorded privately; the safe projection explicitly reports partial recovery,
`reference_integrity=false` and `source_missing_reference_count=220`. Current
source-bucket versioning was never enabled; other historical media is not thereby
proven absent. No green complete-reference claim is made.

A fresh exact relative-key-hash join found the recovered 55 comprise 54 confirmed
and one pending record; the remaining 220 comprise one confirmed and 219 pending.
The count coincidence does not mean all confirmed documents were recovered.
The 55-blob supplement is a persistent protected plan input, not a temporary task
cache: root-only directory/files, sealed manifest and every blob SHA were read back
at 01:10. Missing/corrupt input rejects a new point and preserves prior evidence;
it cannot silently downgrade to a 275-gap successful point.

Safe receipts are in the task's private audit directory under
`SaaS-platform/audit-2026-10-27/disaster-recovery-completion/alphabet/`, including
`helper-final-evidence-upgrade.json`, `garment-partial-with-55-supplement.json`,
`first-generation-ref-proof-inventory.json`, `online-cycle-2.json`,
`windows-v3-compatibility-actual-reader.json` and
`source-bucket-versioning-readonly.json`, `online-cycle-3-peak-and-retention.json`,
`online-schedule-installed-actual.json`, `garment-55-recovery-status-hash-join.json`
and `final-health-seal-and-safe-source.json`. No archive, credentials or user file
body is committed here. Fixed-command metadata aggregation to the main host is
separately installed by the platform owner; exact source/host/org/runtime/project
identities remain stable.

## Verification

Final targeted tests: Windows 74 passed / 3 POSIX skips; Linux root in an isolated
`/tmp` copy with private venv 77 passed / no skips. This is local Linux evidence,
not a GitHub check or a public stable Skill release.
Tests include a live WAL snapshot with continued writes, FK failures, missing and
corrupt references, traversal rejection, source mutation detection, actual Git
bundle and schema-3 upload/readback/isolated restore, metadata-only observation,
failed-latest/prior-point retention, wrapper preservation and Windows compatibility.
Real points verify data/Git/config hashes and DB/file references in isolated
directories. Full fresh-host service reconstruction, restored business execution,
external NAS/Daoxun originals, Windows fresh-generation ACK and natural daily-timer
execution are not claimed by these receipts. Platform desktop/mobile UI validation
and the common Skill stable release are owned and reported separately by Root.

## First natural daily generation, 2026-10-28

The pending natural-cycle boundary above was closed by the original online timer,
without a manual start or a schedule/code change. It triggered at 03:22:53 CST;
invocation `e8d5d473ecc143b9b45cff7b19e5ac5b` finished successfully at 03:37:15,
862.448399 seconds later. All nine newly captured points have matching point IDs,
archive SHA, exact OSS versions/full readback and real isolated database, Git,
file and restored-database reference checks. Eight reference sets are complete;
garment retains the known 220 unresolved references and partial result. It did not
silently revert to the old 275-gap point or claim complete references.

Every application retained two local v3 points and genuinely pruned one eligible
older v3 point after the required readback/restore checks. Cloud history and
legacy schema-2 history remain. The 782 one-second samples measured minimum free
space 6,330,667,008 bytes and minimum MemAvailable 1,603,526,656 bytes; final free
space was 12,514,779,136 bytes. These are sampled observations, not an unlimited
future capacity guarantee. All nine original business container IDs and PIDs,
healthy state and zero restart counts remain; plan, code, wrapper and unit pins
match the pre-run bytes. The metadata source naturally refreshed at 03:37:55 to
all nine new points. Next timer observation was 2026-10-29 03:22:18 CST; the old
service-stopping timer remains disabled.

The separate Windows secondary export did not complete. Its new preflight refused
capacity at 03:37:18 before the original exporter started: the configured 6 GiB
reserve, at least 2.5 GiB export staging and 5,593,427,971-byte next-primary peak
require at least 14,720,233,475 free bytes; only 12,515,344,384 were available.
This is the added capacity guard's rejection, not evidence of a schema-3 reader
failure or an offline Windows machine. No fresh secondary copy/ACK is claimed.
The protection was not lowered, history was not deleted to force it through and
the export was not retriggered. Primary OSS backup and recovery success is
independent of this secondary capacity limit.

Safe receipts are `alphabet/natural-first-cycle-accepted-safe.json`,
`alphabet/natural-first-terminal-complete-metadata-safe.json` and
`alphabet/windows-secondary-capacity-verdict-safe.json` under the task audit.
They contain bounded metadata, not archive bodies or credentials. This natural
run still does not certify full service boot or selective production writeback.
