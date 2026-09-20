# Module 12 rewrite acceptance — 2026-09-19

Working-tree candidate, not publication or human-learning acceptance.
Archive: `north-echo-evidence-v2-20260919.tgz`.
SHA-256: `4ca9b86fc9194e71b72d33ad57914e55cca6a22e1c74b99d2c8ccd704641af33`.
Fedora 44 ARM64, kernel 6.19.10-300.fc44.aarch64, SELinux enforcing, in the
isolated installer-validation VM on the previously pinned image.

- Strict full suite: **126 passed, no skips**, 30.515 seconds.
- Canonical attestation and manual synchronization: PASS.
- Behavioral preflight: **33 passed, 0 failed**.
- Actual guided command replay: fixed baseline omissions; one/two-action
  comparison; offline missing, unknown, contrary, and duplicate evidence;
  package missing/changed input refusal, repair, relocation, deterministic
  replay, and existing-directory refusal.
- Additional tests reject malformed reviewer rows and non-allowlisted
  inventory paths. No packaged code executes during integrity verification.

The label oracle supplies its own answer. This establishes bounded synthetic
dispatch, not independent discovery or real containment measurement. The offline
reviewer classifies supplied fixtures, not newly collected kernel evidence.
Package hashes are unsigned byte inventories, not authenticity guarantees.
No external target or real credential was used. Original learner VM untouched.

Follow-up cross-course review found incorrect independent-lab preparation paths
in Modules 08-12. This gate did not test those preparation commands; correction
and a new actual-command regression are required before the final beta gate.
