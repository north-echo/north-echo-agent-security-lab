# Module 11 rewrite acceptance — 2026-09-19

Working-tree candidate, not a published release or human-learning acceptance.
Archive: `north-echo-model-v2-20260919.tgz`.
SHA-256: `feda3ec2c17fb7d6c5fcbbd25fe3a4551b47c946c0754cbeaadabf95c055cf92`.

Fedora 44 ARM64, kernel 6.19.10-300.fc44.aarch64, SELinux enforcing,
isolated Lima installer-validation VM; same pinned image and packages as
`../fedora-installer-20260919/RESULTS.md`. Original learner VM untouched.

- Strict full suite: **121 tests passed, no skips**, 29.438 seconds.
- Canonical attestation: PASS; field-manual synchronization: PASS.
- Linux behavioral preflight: **33 passed, 0 failed**.
- All three Module 11 documented noninteractive command sequences replayed,
  including partial repair, complete repair, preservation, exact comparison,
  and incomplete-evidence refusal.
- Additional regressions reject input aliases/symlink output and preserve an
  existing destination on malformed control types. Existing randomized grader
  checks pass for the guided repair and reject the incomplete starter.

The local harness no longer interprets arbitrary plan literals or forwards
unrelated ambient credentials. The constant marker, generated sibling files,
unconnected socket, and string-only cleanup candidates remain teaching fixtures.
The secure network branch skips creation: this is not kernel-denial evidence.
No external target, real credential, destructive candidate cleanup, or retained
student solution was used. Human comprehension and delayed replay remain open.
