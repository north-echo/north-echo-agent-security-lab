# Gate A Linux validation results

## Decision

**PASS** — Modules 01-03 work end to end on the supported Ubuntu baseline, the completed independent-lab solutions were reset, and no lab-owned runtime artifact remains.

## Source and environment

- Source checkpoint: `08d17121c38ff07bfe8c19982016db73b14ba43e`, plus the focused portability and grader fixes described below.
- Distribution: Ubuntu 24.04.4 LTS (Noble Numbat).
- Kernel: `6.8.0-134-generic`.
- Architecture: `aarch64`.
- VM: disposable Lima 2.2.0 instance using Apple's Virtualization framework; 4 CPUs, 6 GiB memory, 30 GiB disk.
- Execution identity: ordinary user `lima` (UID 501); root was used only for package installation and the documented VM-local AppArmor profile.
- Tool inventory: Python 3.12.3, GCC 13.3.0, strace 6.8, util-linux 2.39.3. See `environment.txt` for the complete captured inventory.

## Gate results

| Gate | Result | Evidence |
| --- | --- | --- |
| 0 — non-destructive preflight | PASS | `preflight.txt`: 20 required checks passed, 0 failed. |
| 1 — control plane and integrity | PASS | Initial 13-test suite passed; final expanded suite passed 17 tests. Course attestation passed before and after fixes. |
| 2 — nine guided paths | PASS | `lessons/01.01.txt` through `lessons/03.03.txt` record the observations, intentional failures, repairs, and checkpoints. |
| 3 — independent graders | PASS | Each starter returned `RESULT: NOT PASSED` in practice and exam modes. Completed implementations passed every property in both modes with fresh evaluation fixtures. |
| 4 — replay and metadata | PASS | `replay-metadata.txt` proves fixture rotation, student-work removal, and metadata-only persistence. |
| 5 — reset and cleanup containment | PASS | `reset-dry-run.txt` and `reset-all-dry-run.txt` prove dry-run preservation and scoped removal. Hostile-path and unrelated-resource rejection tests passed. |
| 6 — final inspection | PASS | Final attestation passed and `final-owned-artifacts.txt` is empty. |

## Defects found and fixed

1. Ubuntu 24.04 enables AppArmor's unprivileged-user-namespace restriction by default. A narrowly scoped VM-local profile grants `userns,` only to `/usr/bin/unshare`; the global restriction remains enabled. The exact profile is retained as `apparmor-north-echo-unshare`, and `apparmor-userns-restriction.txt` records the enabled global setting.
2. Lesson 03.02 incorrectly requested `setpriv --clear-groups` after `unshare --map-root-user`. The kernel disables later `setgroups(2)` calls for that safe single-ID mapping path, so the documented command failed with `EPERM`. The lesson and field manual now treat supplementary groups as a separate authority channel and test capability reduction independently. A Linux regression test exercises the corrected command.
3. The Module 02 grader required at least two `NSpid` values. A procfs mounted from inside the child PID namespace correctly reports only `NSpid: 1` on this baseline. The grader now accepts a nonempty namespace-relative PID list ending in 1 while still requiring a PID-namespace inode distinct from the grader. Three focused tests cover the valid and invalid cases.

## Skips and limitations

- No Gate A step was skipped.
- Lesson 02.03's short-lived child was reaped before the snapshot, so no zombie row appeared. The namespace PID 1 and matching procfs properties still passed; exact transient process counts are intentionally not graded.
- This record validates Ubuntu 24.04.4 LTS on arm64 only. Debian 12 and x86-64 remain unvalidated.
- The AppArmor exception is VM-local and deliberately limited to the course's `unshare` executable. It is not a recommendation for a general-purpose workstation.

## Safety and retention confirmation

- Only synthetic local fixtures and loopback/isolated VM resources were used.
- No personal, employer, cloud, or production credential or external target was used.
- Raw validation logs were scrubbed of the host repository path and generated canary values.
- Completed student implementations were removed by the tested reset paths and were not retained in this record.
- `.student`, `.fixtures`, and `.runtime` contain no generated artifact after final cleanup.
