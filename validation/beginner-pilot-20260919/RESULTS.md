# Beginner pilot mechanical acceptance - 2026-09-19

## Revision and environment

- Uncommitted B0/B1 working tree based on `a6f62ce2f973fac4aa3604ee4abe82af136317b7`.
- Accepted transfer snapshot SHA-256:
  `8c1c2fdd4b08c62307a97b450f55c8ace0a07d45b22636f11283bcbac8eb630b`.
- Canonical course manifest SHA-256:
  `f4cfc6fcd9469ce1ab1056e237a1162da164e0aa8c7ef5b51f4764ea11c26ad1`.
- Separate disposable Lima instance; no host mounts, guest agent, or SSH agent
  forwarding. Existing user VM was not changed.
- Ubuntu 24.04.5 LTS, Linux `6.8.0-139-generic`, aarch64, Python 3.12.3,
  GNU nano 7.2. Ordinary non-root guest user.
- Image: pinned Ubuntu release-20260911 arm64 cloud image from
  `deploy/north-echo.yaml`, digest
  `sha256:7b682958a67ff5de068e36de6af8b75fa645d296af5a70d6500527f6a33781db`.
  Package installation updates the guest beyond the original image; the runtime
  baseline above is the measured environment, not an assertion of frozen packages.

The snapshot precedes this evidence record and final handoff-only notes. It is
not a release archive or a published commit. The default appliance remains v1.0.2.

## Accepted results

Commands were run from the separately extracted candidate root, not the
appliance's preinstalled v1.0.2 course. Selected terminal output:

```text
python3 scripts/run_tests.py --require-no-skips
Ran 73 tests in 13.433s
OK

./scripts/attest-course
COURSE ATTESTATION: PASS

python3 scripts/build_field_manual.py --check
FIELD_MANUAL.md is synchronized

./scripts/linux-preflight
openat2 works; Landlock ABI 4 enforces read policy; seccomp enforces EPERM
SUMMARY: 33 required checks passed; 0 required checks failed
```

The ten new beginner tests cover all six guided exercises and their changed
inputs/repair observations; fresh evaluations of valid implementations; starter
and deliberately incomplete repairs; missing/malformed sources; all eight
targets' start/resume; report fixture rotation; lesson/module/all reset scopes;
dry-run preservation; practice/exam feedback; tamper rejection; temporary grader
cleanup; and metadata-only retention. A separate new manual test verifies
nested source refresh, repeated-render stability, and cycle rejection.

The incomplete repairs rejected include: fixed report path, added newline,
false success on read error, full environment copy, empty environment, deletion
of just one known key, hard-coded public style, fabricated output without a
child, swallowed child status, and suppressed child streams.

A direct CLI smoke additionally started B0.01, previewed its reset, confirmed
reset, and inspected the managed directories. `.student`, `.fixtures`, and
`.runtime` were empty afterward; no `north-echo-*` user units remained. Automated
reference implementations existed only in owned temporary test directories,
which were collected. No student solutions or generated private values are
retained in this evidence record. All worker data and evaluation settings were
synthetic; no real credentials or external targets were used.

macOS control-plane run: 73 discovered, 58 passed, 15 expected Linux-only skips.
The final beginner-only run after bounded witness parsing passed all ten tests.
The host preflight correctly refused non-Linux execution. These host results
are not a Linux validation substitute.

## Defects caught before acceptance

- Existing documentation tests assumed exactly 36 lessons and the old package
  list. Updated expectations to 42 (including six pilot lessons) and nano, and
  accepted the pilot's inline line-by-line labels alongside existing headings.
- The first explicit transfer recipe omitted `.north-echo-root`. Lifecycle
  commands correctly refused to run; that first Linux suite was **not** a pass.
  The corrected recipe includes the marker and support files. Acceptance was
  rerun from a fresh extraction, not repaired by bypassing the safety check.

## Remaining gates

Mechanical acceptance passed on this arm64 Linux baseline. No new x86-64 run
was performed for the pilot. No human beginner walkthrough, delayed recall
assessment, or evaluation of the later course's pacing has occurred. These
results do not establish learning effectiveness or hostile-code containment.

The next gate is the user's B0 diagnostic/optional refresher and B1 practical,
including predictions, explanations, changed-case transfer, and feedback about
where guidance was needed. Do not rebuild the remaining modules merely because
this test suite is green. No commit, push, release, or replacement PDF was made
as part of this pilot implementation.
