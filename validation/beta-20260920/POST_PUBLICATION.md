# Actual beta.1 publication and corrected-installer acceptance

## Immutable publication

Tag `v2.0.0-beta.1` points to commit
`63defa2c036fbfd6e48cdb96c344bc7acbf443ca`. Both Ubuntu x86-64 and ARM64 jobs
passed for [main](https://github.com/north-echo/north-echo-agent-security-lab/actions/runs/35488522483)
and the [tag](https://github.com/north-echo/north-echo-agent-security-lab/actions/runs/35515971636).
The prerelease is published with six assets; tag and artifact bytes were not
replaced after the deployment defect below was found.

Source archive SHA256:
`88acf0f7d6842a9ccca0b15c70363a3ddd616095bc73b7849ce11b641fe64154`.
PDF SHA256: `2e68b35b09e0b94fce947edf99ac86b55da72f1df221310d00c6096cfcbe7cb3`.
All five artifact checksum entries and the complete Git bundle verified.
The release-built PDF passed automated checks, and all 271 rendered pages were
pixel-identical to the visually inspected candidate. The PDF's original setup
instructions use the beta.1 tag and therefore inherit its installer defect.

## Original fresh-install failure

The original Fedora template downloaded and verified the real beta.1 archive,
then discovered 132 tests: one failure and one error, 33.474s. Readiness was
correctly withheld. The disposable failed installation was stopped; no learner
work or original VM was changed. The release page carries a prominent warning.

1. Its inline `python3 -` runner left an unimportable `<stdin>` main module.
   Python 3.14's forkserver worker attempted to import that nonexistent path.
   The concurrency test failed instead of silently skipping.
2. Provisioning ran in `system_u:system_r:cloud_init_t:s0`, unlike the learner's
   ordinary `unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023` session.
   Executing `ip` transitioned to `ifconfig_t`; the SELinux audit denied
   namespace-local `net_admin` and writing the redirected observation file.
   This is not evidence that the lesson needs SELinux disabled.

The unchanged released course then passed 132 tests, zero skips, 37.351s, through
its file-backed runner in an ordinary SSH session. Primary context:
[Python multiprocessing requirements](https://docs.python.org/3/library/multiprocessing.html)
and [SELinux process domains](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/selinux_users_and_administrators_guide/sect-security-enhanced_linux-targeted_policy-unconfined_processes).
The exact Fedora diagnosis above comes from the guest's traceback, `id -Z`,
and audit log, not an inference that all Fedora policy matches RHEL documentation.

## Corrected template, unchanged published archive

Both working templates now invoke `scripts/run_tests.py --require-no-skips`
through the ordinary learner's user manager. The validation unit has an exact
name, literal argv, course working directory, wait/collection, and a 600-second
runtime backstop. No SELinux policy change, forced process label, or enforcement
disablement was made. The strict runner also rejects empty test discovery.

A second fresh Fedora instance used the corrected template to install the exact
published beta.1 archive above. It passed 132 tests with zero skips in 36.074s,
all 33 preflight checks, integrity/manual checks, warning-clean Landlock compile,
empty runtime, and successful readiness. The pinned image/kernel and packages
are recorded in `corrected-installer/`; its environment context is the
provisioning context, not a claim about the user-manager test process.

The separate installer-fix candidate archive
`north-echo-installer-fix-20260920.tgz`, SHA256
`6e994e8e60c630e82a60bede17cd97b6ef79b421644730e2f1b9ebc84feb4367`,
passed 135 tests with zero skips in 34.487s, integrity, and manual sync on Fedora.
The three new regressions guard the invocation context and strict-runner results.
This result must not be described as 135 tests in the unchanged beta.1 archive.

Plain-mode evidence export via `limactl copy` succeeded. Guest and host digest:
`2c53befa7a4fdefacf4b33c3b2e86e82f970be5b89603711b372c433cf7e5f66`.
Only inspected text records are retained; the compiled smoke binary is omitted.
A normal stop/start preserved both the synthetic B0.01 note/source hashes and
readiness-marker mtime. SELinux remained enforcing and course integrity passed.

Replacing only this disposable instance's readiness script with `exit 1`, then
starting with a 45-second timeout, returned exit 1. The instance remained
Running: failed readiness is not a power-off operation. After explicitly
stopping it, restoring the exact original probe, and restarting, readiness
passed again. The same source/note hashes and marker mtime (`1789914323`) still
matched. The synthetic B0.01 acceptance workspace and fixture were then reset;
managed runtime was empty, integrity passed, and SELinux remained enforcing.
No original learner work was deleted. The acceptance note was synthetic only;
the lesson can be recreated with `lab-start`.

A corrected-version publication awaits the user's beta.2 decision; do not
silently move the published beta.1 tag. The corrected template currently
installs the unchanged beta.1 course; it is not part of beta.1's immutable source
archive. Until a replacement tag, use the corrected template from `main` as
described by its README warning.
