# Roadmap

## Completed

- v0.1 - platform lifecycle, Modules 01-03, Gate A (arm64). Record: `validation/RESULTS.md`
- v0.2 - Modules 04-06. Record: `validation/tranche-01/RESULTS.md`
- v0.3 - Modules 07-09. Record: `validation/tranche-02/RESULTS.md`
- v0.4 - Modules 10-12. Record: `validation/tranche-03/RESULTS.md`
- v1.0 - cold capstone, field manual, release workflow, Gate D. Record: `validation/gate-d/RESULTS.md`
- v1.0.1 - runtime-containment framing, continuous x86-64 and arm64 CI, release hygiene, and Landlock filesystem-right coverage through ABI 9 when exposed by build headers
- v1.0.2 - pinned plain-mode Lima appliance, idempotent provisioning, shared CI prerequisites, checksum-verified course installation, readiness probing, and SSH-based evidence export

## Post-1.0.2

### Active v2.0.0-beta.2 installer correction

User authorized the narrow follow-up: corrected installer and strict runner,
consistent beta.2 instructions/manuals, and exact-release fresh Fedora acceptance.
See `validation/beta2-20260920/RESULTS.md`. Preserve beta.1's tag and existing
learner VMs. Independent learner review remains the next gate, not a new feature
tranche or an expanded OS matrix.

### Historical v2.0.0-beta.1 rewrite

Published beta.1 has a documented installer defect, with a corrected template
validated separately against the unchanged archive. See
`validation/beta-20260920/POST_PUBLICATION.md`; replacement beta.2 is pending
user direction. Do not mistake green source CI for fresh-install acceptance.

The user authorized the full rewrite and chose a learner-review beta on
2026-09-19, superseding the earlier B0/B1-only scope below. Fedora 44 ARM64 is
the preferred new-install beta baseline; preserve the existing Ubuntu VM.
B0/B1, Modules 01-12, capstone, setup, source/version companion, and learning
path are reconciled. The 271-page candidate PDF passed rendered layout and
automated checks. Final Linux/artifact acceptance and publication are recorded
in `validation/beta-20260920/RESULTS.md` rather than inferred from earlier runs.
The exact ledger and release gate are in `docs/dev/V2_REWRITE.md`.
Automated acceptance does not replace learner walkthrough and delayed replay.

### Earlier exploration and deferred work

The following exploration entries are historical; their former scope and default
OS restrictions are superseded by the authorized full beta above.

- Fedora exploration: isolated Fedora 44 ARM64 trial passed 76 strict tests and
  33 preflight checks with SELinux enforcing, without course-code changes.
  Record: `validation/fedora-trial-20260919/RESULTS.md`. Ubuntu remains primary;
  Fedora release provisioning, documentation/source review, architecture scope,
  and learner walkthroughs remain migration gates.

- Beginner-entry rebuild: B0 refresher/test-out and B1 environment-handoff pilot,
  with an independent practical for each. Plan and acceptance:
  `docs/dev/BEGINNER_REBUILD.md`. Preserve the existing technical track and gate
  further rewriting on the user's walkthrough, explanation, and delayed replay.
  The pilot is unreleased; do not advertise it as part of the v1.0.2 appliance.
  Initial mechanical acceptance: `validation/beginner-pilot-20260919/RESULTS.md`.
  Latest depth/source revision: `validation/beginner-pilot-20260919/DEPTH_AND_SOURCES.md`
  (76 tests, no skips on Ubuntu arm64). Explicit file-access instruction,
  claim-level primary references, and qualified evidence are now acceptance
  requirements. Human learning validation remains open.

Audit implementation: `docs/dev/AUDIT_IMPLEMENTATION.md` records the unreleased
cleanup/grading/readiness fixes, distinct transfer capstone, offline evidence
comparison and replay, manual synchronization, progress transactions, and learner
diagnostic/fading/checkpoints. Human pilot outcomes remain pending real participants;
see `docs/dev/LEARNER_PILOT.md`. Do not treat automated passes as learning evidence.

- Debian 12 baseline run on x86-64 with a recorded validation entry.
- Module 12 further depth: optional future work beyond the implemented offline evidence comparison; no autonomous probing extension is required for graduation. See `docs/dev/SPEC_v1.0.1.md` section 5 for historical intent.
- Landlock ABI 4 network rules as an optional Module 08 exercise on kernels supporting that ABI.
