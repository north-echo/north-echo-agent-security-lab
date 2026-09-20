# Module 09 rewrite - Fedora validation

Date: 2026-09-19. Working-tree candidate archive SHA-256:
`4d4ad4075dabd0811e21ea35fc8074d3fce6bb0e6a6d3e4048e647523c3e249b`.

Dedicated Fedora 44 ARM64 validation VM, kernel 6.19.10-300.fc44.aarch64;
baseline and SELinux configuration are recorded in the adjacent Fedora evidence.
The original learner VM was not changed.

- 110 tests passed with zero skips in 27.485 seconds.
- Course attestation passed after tests.
- Manual synchronization passed.
- All 33 required preflight checks passed.
- New tests replay the documented environment regression/repair, readable
  authenticated claims, binding mismatch, expiry, repeated stateless
  verification, broker nonce consumption, mismatched-resource repair, and
  registered service/socket cleanup.
- Pure mechanism tests separately verify deterministic input serialization,
  mint lifetime bounds, and binding distinct from token authentication.

The earlier candidate passed the behavioral tests but failed a documentation
heading-presence check for 09.02. The explanation heading was aligned with the
repository convention; no test was removed or weakened. The complete rerun above
passed. The expanded prose distinguishes HMAC from encryption/asymmetric
signatures, process-local replay state from durable consumption, and same-account
teaching roles from an independently isolated credential-storage boundary.

No production secrets, external services, persistent replay guarantee, or
human-learning acceptance are claimed. Modules 10-12 and final release gates
remain outstanding. This is not a published beta.
