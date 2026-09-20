# Fedora-first curriculum rewrite and release gate

Authorized by the user on 2026-09-19: "Rewrite all the materials then new release."
This supersedes the earlier limit to a B0/B1-only prose pilot, but does not
turn automated checks into evidence of learner comprehension.

## Scope

Rewrite learner-facing setup, module introductions, guided lessons, independent
practicals, learning path, capstone guidance, and assembled field manual around
the positively reviewed B0.02 depth. Preserve working code unless a correctness,
portability, or curriculum-alignment defect requires a tested change. Historical
release notes and validation evidence remain historical, not silently rewritten.

Fedora 44 ARM64 is the proposed preferred new-install baseline; Ubuntu remains
available. Do not overwrite or migrate the user's existing VM. x86-64 Fedora
support must not be inferred from ARM64 results. No real targets or credentials.
Later research material must remain bounded, synthetic, and focused on defensive
control verification and interpretation of evidence, not an expanded autonomous
offensive workflow.

## Completion ledger

**Active: v2.0.0-beta.2.** The user authorized the narrow installer-correction
release and exact-artifact Fedora acceptance on 2026-09-20. Current gates and
results live in `validation/beta2-20260920/RESULTS.md`. No new curriculum or
platform support is included. The following beta.1 ledger is historical.

Post-publication status supersedes the prepublication rows: beta.1 and PDF are
published with green dual-architecture CI, but its original fresh Fedora install
failed. Corrected templates pass fresh installation of the unchanged archive;
the fix candidate passes 135 tests. See `validation/beta-20260920/POST_PUBLICATION.md`.
The release page warns about the defect; beta.2 publication awaits user direction.

| Area | State |
| --- | --- |
| Fedora release installer | v1.0.2 bootstrap passed clean install, restart preservation, negative readiness, plain-mode evidence export; beta archive retest pending |
| Fedora setup and source-version review | Complete for tested ARM64 beta; source/version companion and qualified evidence map in docs/SOURCE_TRUTH.md |
| B0/B1 material | Complete beta entry; approved B0.02 preserved, Fedora companion added |
| Modules 01-03 | Rewritten and synchronized, including all introductions and bridge regressions |
| Modules 04-06 | Rewritten and synchronized; actual command tests and narrow scope/source review complete |
| Modules 07-09 | Rewritten with owned lifecycle, effective-state observations, explicit security limits, and documented-command tests; 110 strict Fedora tests pass |
| Modules 10-12 | All rewritten; 126 strict Fedora tests pass, including documented command replay, model/evidence limitations, and portable package integrity failures/repairs |
| Independent practical alignment and capstone | All 15 preparation paths tested; capstone rewritten with skill map and incomplete starter, effective per-job memory, exact collection, and validation-before-launch regression; 129 strict Fedora tests pass |
| Manual synchronization and PDF QA | Synchronized; 271-page candidate rendered and visually inspected, automated geometry/text/navigation clean |
| Linux candidate validation and regression | 132 strict tests, 33 preflight checks, integrity/manual/compile/empty runtime pass on Fedora ARM64 and Ubuntu ARM64; validation/beta-20260920/RESULTS.md |
| Release version/classification | User selected beta: v2.0.0-beta.1 |
| Git commit, CI, release artifacts, publication | Not started; gated on completed material and evidence |

## Per-lesson quality gate

Observable outcomes and prerequisites; purpose and vocabulary before execution;
exact preparation and file access; complete small source with local explanations;
command-by-command explanations; expected patterns with variable fields named;
prediction, deliberate failure, repair, and effective-state checkpoint; targeted
troubleshooting; scoped reset; primary-source sections and version limits.
Do not substitute boilerplate, length, or a heading-presence test for this review.

Independent work withholds solutions, not interface or editor instructions.
Map every assessed skill to earlier practice. Add a bridge exercise if missing.
Clarify normal failures versus infrastructure failures and the limits of each
control. Separate reference-implementation success from human learning results.

## Release gate

Record exact source/archive and image hashes, packages, kernel, architecture,
all strict tests and skips, behavioral preflight, integrity and manual checks,
changed guided walkthroughs, clean teardown, reboot preservation, plain-mode
evidence export, and a deliberately failing readiness probe. Render and visually
inspect the manual. Publish only after inspecting the final diff and CI; do not
describe unfinished modules or untested architectures as complete.
