# v2.0.0-beta.2 - corrected installer, learner-review beta

This narrowly scoped prerelease packages the beta.1 installer correction. The
curriculum and canonical course content are unchanged. It remains a beta for
learner walkthrough, not stable teaching-quality or production certification.

## What changed

- Fedora and Ubuntu installers run the importable `scripts/run_tests.py` entry
  point through the ordinary learner's systemd user manager. This fixes Python
  3.14 multiprocessing from stdin and separates learner checks from cloud-init's
  SELinux domain. SELinux stays enforcing; no policy relaxation is introduced.
- Validation requires a nonempty successful suite with zero skipped tests.
  The validation unit has literal argv, an explicit working directory, automatic
  collection, and a bounded runtime.
- README, setup instructions, template version pins, and both field manuals now
  consistently identify beta.2 and a separate `north-echo-beta2` instance.

Beta.1's tag and artifacts remain unchanged, with an installer erratum. Do not
restart an old instance expecting an upgrade or extract over student work.

## Validation and scope

The predecessor correction passed 135 tests on Fedora ARM64 and Ubuntu CI on
x86-64/ARM64. Those results are not substituted for this release's checks.
See `validation/beta2-20260920/RESULTS.md` for the candidate/release gates and
the follow-up actual-release installation record on the main branch.

Acceptance includes the exact packaged archive, fresh Fedora boot, course
integrity, manual synchronization, behavioral preflight, native compilation,
empty managed runtime, student-work-preserving restart, deliberately failed
readiness followed by restoration, and plain-mode evidence export.

Fedora 44 ARM64 on Apple Silicon is the preferred new-install baseline. Fedora
x86-64 is not claimed. Ubuntu CI does not substitute for a fresh Ubuntu appliance
installation; that expanded deployment matrix is outside this narrow release.
The pinned image does not freeze later package-repository revisions.

## Start learner review

Use the README and matching beta.2 manual. Begin at B0.01, predict before running,
and note the first unexplained step or hint needed. Independent practice and
delayed replay remain the learning gates before stable v2.0.0.

Assets: source archive, Git history bundle, Markdown and PDF manuals, release
notes, and SHA256SUMS. Match all artifacts to this tag.
