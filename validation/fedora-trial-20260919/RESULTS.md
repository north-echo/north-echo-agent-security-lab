# Fedora compatibility trial — 2026-09-19

Local date: 2026-09-19 (America/New_York); execution crossed 2026-09-20 UTC.
Result: **promising ARM64 candidate, not a supported-default migration**.
No course source or grader changes were needed for Fedora. Ubuntu deployment,
CI, the existing Ubuntu VM, and the user's student work were left unchanged.

## Exact baseline

- Uncommitted candidate based on `a6f62ce2f973fac4aa3604ee4abe82af136317b7`.
- Candidate transfer archive SHA-256:
  `c160718086cc698ff8e2d37b9395c827ce966cd7860336576c9333c84705fa71`.
  Includes the current B0/B1 pilot, experimental YAML/package list, tests, and
  the `.north-echo-root` marker. This result record and final status/docs were
  added afterward. No `.git`, host credentials, student work, or runtime state
  was transferred. Checksum verified inside the guest before extraction.
- Course manifest SHA-256:
  `ca988948aaa23b19c6a538c21fe41baf197c4da63b19297fe096a61055ce63ce`.
- Lima 2.2.0, VZ, aarch64, 4 CPUs / 6 GiB / 30 GiB, plain mode, no host mounts,
  no SSH-agent forwarding. Separate disposable trial instance.
- Fedora 44 Cloud image:
  `https://download.fedoraproject.org/pub/fedora/linux/releases/44/Cloud/aarch64/images/Fedora-Cloud-Base-Generic-44-1.7.aarch64.qcow2`.
- Image SHA-256:
  `55c60a3b80d3616a08705afd0459e75fe9f03c54aba7a46e4002a41a72fa0d5b`,
  from the installed Lima template; image download verified by Lima.
- Running kernel: `6.19.10-300.fc44.aarch64`; Python 3.14.3; GCC 16.2.1;
  Bash 5.3.9; systemd 259.5; libseccomp 2.6.1. See `packages.txt` for exact RPMs.
  Installed kernel headers are newer than the running image kernel; headers
  do not prove running-kernel support. Behavioral preflight reported Landlock ABI 7.
- SELinux stayed **Enforcing**, with Landlock also present in the active LSM
  list. The ordinary user's context was `unconfined_t`; this is not evidence
  of a confined SELinux user domain or an SELinux-based student sandbox.

The image is pinned but `dnf` packages are not. No global security controls,
SELinux policy, kernel command line, or namespace restrictions were weakened.

## Observed results

| Check | Result |
| --- | --- |
| Initial provisioning and real readiness probe | PASS |
| Linux behavioral preflight | 33 required passed, 0 failed |
| Strict suite, `python3 scripts/run_tests.py --require-no-skips` | 76 passed, 0 skipped; 14.619 s in the retained run |
| Course integrity | PASS |
| Manual synchronization | PASS |
| Canonical Module 05 lesson compilation, `-Wall -Wextra -Werror -O2` | PASS, exit 0 |
| B0.02 file access and runs | `ls -l`, `cat`, success status 0 and deliberate failure status 7; different PIDs with the same parent |
| Ordinary restart in persistent guest home | Prepared lesson hash and package-marker mtime unchanged |
| Post-restart preflight and integrity | PASS |
| Plain-mode SSH evidence export | PASS; guest and host archive hashes match |
| Deliberately failing readiness probe | `limactl start --timeout 45s` returned exit 1; restored probe returned exit 0 |
| Final cleanup | Owned B0.02 workspace/fixtures reset; managed directories empty; no `north-echo-*` user units |

The negative probe test changed only the separate trial instance's probe to
`#!/bin/bash` / `exit 1`, then stopped/started it. Lima did not report readiness
and returned `did not receive an event with the running status` at the deadline.
**A failed start is not an automatic VM shutdown**: the VM remained booted and
was explicitly stopped before restoring the real probe. The repository template
was never changed to the false probe. Restored and normal starts completed in
roughly seven seconds.

Evidence export command:

```bash
limactl copy north-echo-fedora-trial-20260919:/var/tmp/north-echo-fedora-evidence-20260919.tgz /private/tmp/north-echo-fedora-evidence-20260919.tgz
```

Export SHA-256 on both guest and host:
`e577211b585990feaed1d6b614315044fe76d45d9400b48b06013bf8adc25975`.
Only reviewed text outputs are retained here; the compiled smoke-test binary,
fixture metadata, and prepared student program are not part of this record.
The trial VM was stopped, not deleted, after validation.

## Differences found, and what they mean

1. **Package names differ.** Fedora needs explicit `glibc-static` and
   `libseccomp-static`, in addition to `libseccomp-devel`. The separate manifest
   installed all prerequisites successfully. No Ubuntu/AppArmor workaround was
   needed.
2. **Scratch storage is not persistent.** The first validation extraction used
   `/tmp`; `findmnt /tmp` confirmed tmpfs, and a reboot removed that scratch
   extraction and its logs. No user work was involved. The retained run repeats
   the full suite with the course under the guest home and evidence under
   `/var/tmp`; the subsequent restart preserved the lesson checksum and marker.
   Keep student work under the guest home, as the Ubuntu appliance already does.
3. **Inventory command differs.** The initial harness tried `systemd --version`,
   which was not on this guest's PATH. It was corrected to `systemctl --version`
   before the full checks. This was a validation-harness issue, not a course defect.
4. **Userspace is newer.** Current tests passed with the recorded newer Python,
   compiler, and systemd, but the Ubuntu-specific source links and package/setup
   instructions are not yet a reviewed Fedora teaching baseline.

## Scope and remaining gates

This establishes mechanical compatibility for this ARM64 image and candidate,
including automated B0/B1 guided observations and existing full-course tests.
It does not replace manual execution of every guided lesson or an independent
learner's practical. No Fedora x86-64 test, Fedora CI job, tagged-release
installer, package lock, PDF regeneration, or full source-reference review was
performed. The trial readiness marker certifies OS prerequisites only, not course
acceptance. Ubuntu remains the supported default.

Before making Fedora primary: complete the learner walkthrough, review all
distribution-specific instructions/source mappings, implement and accept the
release installer with work-preserving readiness semantics, and decide the
supported architectures and kernel-validation cadence. Do not imply that a
Fedora container on an Ubuntu CI runner validates a Fedora kernel.

Host checks also passed: 76 tests discovered, 61 passed, 15 expected Linux skips;
course integrity, manual synchronization, YAML validation, and whitespace checks.
Only synthetic local fixtures were used. No real credentials or external targets,
and no completed student solutions, are retained. No commit, push, or release.
