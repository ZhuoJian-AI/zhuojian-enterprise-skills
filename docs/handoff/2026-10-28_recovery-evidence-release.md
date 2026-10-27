# Recovery evidence contract: stable release and scoped installation

## Published source and assets

Core 1.1.50 was merged through PR #100 as
`433b66966ccb539bcc87b47ea8dc229c80f6f9b4`. The exact PR run
40549166111 and merged-main run 40549766915 succeeded. Canonical core selection
passed 970 tests with 78 conditional skips and one warning; the separately selected
company maintenance tests passed five with one Windows symlink skip. The original
core test selection and contracts 2.4/2.5 remain unchanged. Company maintenance
tests live outside the independently installable core Skill.

Stable [bundle-v1.4.53](https://github.com/ZhuoJian-AI/zhuojian-enterprise-skills/releases/tag/bundle-v1.4.53),
Release 425783605, was published at 2026-10-27 17:36:47 UTC
(2026-10-28 01:36:47 CST). Its published tag resolves to the merged source above.
The clean LF build produced core ZIP SHA-256
`3c6a1a76680c23289e6c87cc2d706eae8b587953cbe6723fac309be793382e8f`
(809,154 bytes, 189 entries). All eleven official assets were anonymously
downloaded in full and compared with local size/SHA and GitHub's asset digest.
The six unrelated Skill ZIPs and bootstrap reuse the exact previous-release
bytes after a content/metadata comparison proved the clean LF rebuild differences
were solely line endings. The release catalog and manifests name their actual
published hashes. Source is not the update channel.

## Original updater and both Windows accounts

The unmodified public updater, using the default latest manifests, completed fresh
core 1.1.50 installation, 1.1.49 to 1.1.50 upgrade, subsequent CURRENT checks and
the legacy 1.2.0 entry. Six commands exited zero without stderr warnings. Both
core installations match all 189 public ZIP entries; the legacy installation
matches all eleven. The latest manifest/catalog and legacy archive link were
read back independently, without test-URL or manifest overrides.

Only the sixteen authorized core paths changed from the recorded base were
synchronized to each Windows account. Each old path was backed up, checked
against its expected prior content and atomically replaced; all other files in
both Skill directories retained their original bytes. Four pre-existing codex02
line-ending differences were inspected rather than overwritten wholesale. The
original updater then reported `SKILL_UPDATE_CURRENT 1.1.50` for each real account.
No credentials, access profiles or other personal Skills were synchronized.

## Runtime evidence is separate

The common contract now requires an actual data-location inventory, online
consistency declaration, exact offsite full readback, attachment bodies plus
database-reference checks, private configuration and source recovery inputs,
per-system evidence and preserved failures. It distinguishes a shared whole-host
point from a selective tenant restore and forbids describing a listing or a
valid archive alone as verified recovery.

Alphabet's authorized Runtime installation is documented in
[the runtime handoff](2026-10-27_alphabet-online-disaster-recovery.md). Nine systems
were backed up without stopping their business containers; actual isolated
database, Git, file and reference checks were repeated across three generations,
with two verified local points retained. The original Runtime helper and business
container identities were preserved. The new online timer was installed at
01:08:41 CST; its first natural trigger was still pending at this release's
acceptance checkpoint. Manual validation cycles are not natural timer evidence.

Garment's source already lacked 275 referenced attachments. Fifty-five exact
historical bodies were recovered into backup only, leaving 220 unresolved
(one confirmed and 219 pending business records). Its point remains partial with
failed reference integrity; the live source was not silently repaired. New
unrecognized gaps or a corrupt/missing supplement reject the new point while
preserving prior evidence.

Main-host backup/restore helpers belong to the separate deployment Skill. The
SaaS metadata collector and administrator page belong to Console/Control. Their
publication, runtime installation, actual recovery and desktop/mobile acceptance
are recorded separately. This release does not certify a fresh-machine service
boot, external NAS/Daoxun originals, selective SaaS tenant writeback, production
cutover, physical phones or the independent COA server.

Safe release, updater and two-account receipts remain under the task's private
audit directory `disaster-recovery-completion/root/`; no business archive, file
body, credential or customer configuration is included in this repository.
