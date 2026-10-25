# Gateway Runtime profile compatibility

The gateway's new shared-bucket namespace preflight rejected every existing
root-owned Runtime profile with mode 0640 or 0644, although the host installer
explicitly accepts 0600, 0640 and 0644 and Runtime updates preserve that mode.
This prevented a valid installed Runtime from upgrading its storage gateway.

`configured_namespace` now checks Runtime identity as non-secret metadata:
regular file, root owned, and no group/other write permission. Symlinks and
non-root ownership remain invalid. OSS credential loading is unchanged and
still requires 0600 or stricter.

The independent branch is based on Skill source `2710a57`. Local
`compileall` and `git diff --check` passed. Thirteen new Linux/root cases
cover existing 0600/0640/0644 metadata in shared and legacy modes, all
group/other writer combinations, symlinks, directories, non-root ownership,
and unchanged credential restrictions. The root coordinator will freeze the
merged source and run these with the affected gateway and backup suites;
actual Linux results are recorded in the overall multi-owner handoff.

This commit changes the Skill's gateway template only. No enterprise profile,
running gateway, release asset or personal Skill installation was modified.
Publication, installation, and the two-account synchronization remain with
the root coordinator.
