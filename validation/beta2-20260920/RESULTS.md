# v2.0.0-beta.2 narrow release validation

User selected option 1 on 2026-09-20: package the installer correction, update
release/setup/manual references, and validate the exact release in a fresh
Fedora VM. No new curriculum or supported-architecture claim is included.

## Scope and gates

Canonical `course/` files and their manifest must remain unchanged from beta.1.
The technical gate is separate from human learner review. Prior evidence is in
`validation/beta-20260920/POST_PUBLICATION.md`; it is not a beta.2 result.

- Prepublication: host regression, integrity/manual synchronization, template
  validation, rendered PDF review, clean commit and dual-architecture Ubuntu CI.
- Artifact gate: tag/HEAD/version match, source archive and Git bundle checks,
  five SHA256SUMS entries, correct PDF version/navigation/layout.
- Actual-release gate: fresh pinned Fedora ARM64 instance downloads and verifies
  the published beta.2 archive, executes every test without skips, and passes
  preflight, native compilation, integrity, manual synchronization and cleanup.
- Lifecycle gate: normal restart preserves synthetic student work and marker;
  deliberately failing probe makes start fail; restoration succeeds; plain-mode
  evidence export has equal guest/host digest.

Record observed results below as each gate completes. Post-publication evidence
will be committed separately; never move the release tag to add later evidence.
The existing learner VM and beta.1 tag/artifacts must remain unchanged.

## Prepublication observations

- Candidate archive `north-echo-beta2-candidate-20260920.tgz`, SHA256
  `1ae3b70e74305fa9df2a1795bc0b8a800746c0edae6169b8057a22a087cc2189`:
  Fedora 44 ARM64, kernel 6.19.10-300.fc44.aarch64, SELinux enforcing,
  135 tests passed without skips in 34.959s; 33 preflight checks passed;
  integrity, manual synchronization and empty managed runtime passed.
- macOS: 135 discovered, 95 passed, 40 expected Linux-only skips in 33.819s.
  This is control-plane evidence, not Linux containment validation.
- Both beta.2 Lima templates validate with Lima 2.2.0. Canonical course and
  manifest have no diff against beta.1. PDF QA found no geometry, glyph or
  navigation problems; setup commands received explicit shell continuations
  and a reset-section page break after rendered review.

This snapshot precedes final documentation/formatting and evidence updates;
CI and the actual-release install validate the final tagged source separately.

## Published artifact acceptance — 2026-09-20

Release: https://github.com/north-echo/north-echo-agent-security-lab/releases/tag/v2.0.0-beta.2

- Tagged commit: `545004918872194864be7f382ed0195fff187d87`.
- Source archive SHA256:
  `ddcc176c3eb5a4fb55938dce6b44335ea5f8983af6b6c2d865468df0a67e5f68`.
- PDF SHA256:
  `4a05663efc08b30061d1bc23a6466a72ffe069df113a9b6bed558dbc60f1018e`.
- All five SHA256SUMS entries and the complete-history Git bundle verified.
  GitHub's six asset digests matched local files. Published as a prerelease,
  not the latest stable release; beta.1's tag and assets were not changed.
- Ubuntu 24.04 x86-64 and ARM64 CI passed for the tagged commit:
  https://github.com/north-echo/north-echo-agent-security-lab/actions/runs/35521549754
- Canonical `course/` including its manifest is unchanged from beta.1.
- The 271-page PDF passed text, geometry, bookmarks and link checks. All pages
  were rendered and reviewed in contact sheets; changed setup pages were also
  inspected at reading resolution. Final release renders matched the reviewed
  candidate page-for-page. This is layout QA, not a learning-outcome result.

### Exact release in a fresh VM

Created a new `north-echo-beta2` instance from the tagged Fedora template using
Lima 2.2.0 on Apple Silicon: 4 CPUs, 6 GiB RAM, 30 GiB disk, plain mode, no host
mounts or agent forwarding. The default installer downloaded the actual
published archive and verified its checksum; no candidate archive was substituted.

Pinned image:
`https://download.fedoraproject.org/pub/fedora/linux/releases/44/Cloud/aarch64/images/Fedora-Cloud-Base-Generic-44-1.7.aarch64.qcow2`

Image SHA256:
`55c60a3b80d3616a08705afd0459e75fe9f03c54aba7a46e4002a41a72fa0d5b`.

Observed Fedora 44 ARM64, kernel 6.19.10-300.fc44.aarch64, Python 3.14.3,
GCC 16.2.1, systemd 259.5, libseccomp 2.6.1, Landlock ABI 7. SELinux remained
enforcing. The environment log records the provisioning `cloud_init_t` domain;
the strict suite is launched through the learner's systemd user manager, not
that provisioning domain. This does not claim per-lesson SELinux confinement.
Actual package revisions are retained in `deployment/packages.txt`; the pinned
image does not freeze package repositories.

- Fresh startup returned zero after provisioning and readiness.
- **135 tests passed, zero skips, 33.509s** (`deployment/tests.txt`).
- **33 required preflight checks passed, zero failures**, including effective
  Landlock/seccomp enforcement and delegated cgroup limits.
- Integrity and manual synchronization passed. The canonical Module 05 C
  program compiled with `-Wall -Wextra -Werror`; its binary was present in the
  exported archive but is intentionally not committed as evidence.
- Managed student, fixture and runtime directories were empty after validation.
- Plain-mode `limactl copy` exported the evidence archive successfully. Guest
  and host SHA256 were equal:
  `224e58a4d144dfe404276e6fe7e0314cdc28e7be0650b5fd527f0241f3abd0e2`.

### Lifecycle acceptance

1. Started B0.01 and added only a synthetic preservation note. Recorded hashes
   of the note, workspace README and readiness marker, plus marker modification
   time. Normal stop/start returned zero; all hashes and marker time matched.
2. Stopped this validation VM, temporarily replaced only its readiness probe
   with `#!/bin/sh` followed by `exit 1`, then ran
   `limactl start --tty=false --timeout 45s north-echo-beta2`.
   Startup returned **1** without declaring readiness. The VM remained running:
   a failed readiness probe is not automatic power-off or an access-control gate.
3. Explicitly stopped the VM and restored the exact tagged probe. Startup
   returned zero. Student hashes, marker hash/time and course attestation passed
   again; provisioning did not overwrite student work.
4. Ran only `./lab-reset b0.01 --yes` for the synthetic acceptance workspace.
   Student work and fixtures were removed (not retained as a solution); allowed
   attempt metadata remains. Managed directories were empty, attestation passed,
   and the transient validation unit's LoadState was `not-found`.

Only synthetic local fixtures were used; no real credentials or external target.
The original learner VM was untouched. Evidence was recorded after publication
in a separate commit; the release tag and six assets remain immutable.
The accepted `north-echo-beta2` VM is stopped and retained for learner review;
start it with `limactl start north-echo-beta2`, then enter with
`limactl shell north-echo-beta2`. The original `north-echo` VM remains running.

## Remaining gate

Technical beta.2 acceptance passed on the stated baseline. A fresh Ubuntu
appliance and Fedora x86-64 were not tested by this narrow release. Novice
walkthrough, independent practice, feedback repair and delayed replay remain
required before stable v2.0.0; automated acceptance cannot establish comprehension.
