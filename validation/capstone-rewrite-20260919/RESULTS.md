# Capstone and cross-course preparation — 2026-09-19

Candidate archive: `north-echo-capstone-v2b-20260919.tgz`.
SHA-256: `78f699ac54a9d1d69eff858188ab69cf619301f0d1305905a88c3ffed3f903dd`.
Working tree, not a published release. Fedora 44 ARM64,
6.19.10-300.fc44.aarch64, SELinux enforcing, isolated validation VM.

- Strict full suite: **129 passed, no skips**, 35.056 seconds.
- Canonical attestation and manual synchronization: PASS.
- Linux behavioral preflight: **33 passed, 0 failed**.
- All 15 independent-lab preparation blocks enter the actual workspace;
  only the interactive editor is omitted by that regression.
- Prepared `10.lab` registration now uses the platform registry, not the
  standalone evaluator record path. An explicit regression covers the branch.
- Capstone observes three independent effective memory limits, ordered 0/7/0
  outcomes, distinct exact unit names, and exact reported-unit absence.
- A deliberate eager-launch implementation is rejected when a later runtime
  spec is invalid. The observer runs at trusted guard entry.

An initial negative test failed because its worker-side marker was prevented
by the correctly read-only guard. Moving the observation before policy
installation made the check measure early launch rather than write authority;
the bad implementation now fails and the valid reference passes. No weakened
guard or broad unit cleanup was introduced.

Original learner VM untouched. All material is synthetic/local. The capstone
starter remains incomplete and no complete implementation is added to its
student workspace. Human rationale scoring and delayed replay remain open.
