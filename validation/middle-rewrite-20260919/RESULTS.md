# Modules 04-06 rewrite candidate: Fedora regression gate

Candidate archive SHA256:
`1825609229a8183e04b3a9c2dfa99a97c6cca3119074944570e596514e479e32`.
Uncommitted candidate; this is not the future beta release artifact.

Fedora 44 ARM64, kernel `6.19.10-300.fc44.aarch64`, SELinux enforcing:

- Strict suite: 95 tests passed, no skips, 16.050 seconds.
- Course attestation: PASS.
- Assembled manual synchronization: PASS.
- Linux preflight: 33 required checks passed, none failed; Landlock ABI 7.

The new tests exercise the actual tool loop and documented failure-aggregation
edit, child/runner status distinction, descriptor-relative file creation and
truncation, Landlock's useful allowed operation plus a simulated descriptor-setup
failure, seccomp's effective state, and rejection of a misspelled action mode.

The Landlock teaching launcher now requires supported range-based close-on-exec
marking instead of weakening that guarantee through a soft-limit-bounded fallback.
The seccomp example distinguishes syscall errno diagnostics from libseccomp's
negative error returns and checks missing process-state fields explicitly.

macOS control-plane suite: 95 tests, 71 passed and 24 expected Linux skips,
24.571 seconds. That result is not kernel-enforcement evidence.

Modules 07-12, learner setup, capstone guidance, final source review, PDF visual
QA, final strict candidate checks, and an actual published-beta clean install
remain pending. Automated evidence does not establish learner comprehension.
