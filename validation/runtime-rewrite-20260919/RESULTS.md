# Module 10 rewrite - Fedora validation

Date: 2026-09-19. Working-tree candidate archive SHA-256:
`0bffd24bd9d3d2e64684bf097029213235d742a1e06499aaacf0aad5819f7649`.

Dedicated Fedora 44 ARM64 validation VM, kernel 6.19.10-300.fc44.aarch64.
Baseline image and SELinux configuration remain as recorded in the Fedora
installer/trial evidence. The original learner VM was not changed.

- 116 tests passed, zero skips, in 29.705 seconds.
- Course attestation and manual synchronization passed after tests.
- All 33 required Linux preflight checks passed.
- Exact documented commands passed for dependency mistakes/repair, inner
  filesystem/syscall composition, incomplete versus complete launch,
  registered broker/workload cleanup, and sequential worker statuses 0/7/0
  with observed per-job memory values.
- Ownership tests reject a foreign description and retain evidence when the
  user manager cannot establish state.
- A new grader regression detects systemd environment expansion of literal
  path arguments; the correct launcher disables it.
- The native guard's narrower /proc/self read grant works on this baseline.
  Its close-on-exec descriptor setup, all-five-capability observation, and
  streamed fixed-fixture broker response passed the composition tests.
- The existing independent batch capstone reference still passes.

An earlier complete candidate passed behavioral tests but failed a documentation
assertion tied to the previous lesson title. The assertion now checks the renamed
lesson, without dropping a content check. The full rerun above passed.

The rewritten chapter explicitly limits its claims: no private PID/mount view,
no ABI 9 Unix-socket-resolution enforcement on the ABI 7 baseline, no full
Module 09 protocol in the small opaque-token composition fixture, no cryptographic
remote attestation, and no independent byte quota on outer output capture.
This is not a production sandbox certification or human-learning acceptance.
Modules 11-12 and final release/artifact gates remain outstanding.
