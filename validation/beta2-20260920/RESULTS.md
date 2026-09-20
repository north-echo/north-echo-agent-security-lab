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
