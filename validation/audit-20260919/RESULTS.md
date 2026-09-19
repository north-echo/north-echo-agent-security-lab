# Audit candidate validation — 2026-09-19

## Scope and identity

Baseline commit: `fa267ef4d3c5b265704b615232a4006d9d0f6a2d`.
The implementation was tested as an uncommitted source snapshot, not a release.
Candidate archive SHA-256:
`4631fc0c4b088e50a8326c371ada5d7e29e29a145a483a138dbba5bd9c596d96`.
Only README/review-record documentation changed after that snapshot; executable
code, course content, and tests match the tested candidate. Generated output,
managed state, Git metadata, and this evidence directory were excluded.

Lima 2.2.0 / vz, plain mode, no host mounts or agent forwarding, 4 CPU / 6 GiB /
30 GiB. Ubuntu cloud image `noble/release-20260911` arm64 digest:
`7b682958a67ff5de068e36de6af8b75fa645d296af5a70d6500527f6a33781db`.
The resulting guest was Ubuntu 24.04.5 LTS, kernel 6.8.0-139-generic, ordinary
non-root user, Python 3.12.3, GCC 13.3.0. Exact installed package revisions are
in `packages.tsv`. Package repositories float independently of the pinned image.

The template booted the checksum-verified published v1.0.2 archive. The changed
source was copied by SSH into a separate validation directory; it did not replace
the released course or a student's work.

## Results

- PASS: `limactl validate deploy/north-echo.yaml` and fresh default-template boot.
- PASS: candidate `python3 scripts/run_tests.py --require-no-skips`: 62 tests,
  zero failures/errors/skips. See `tests.txt`.
- PASS: all 33 required behavioral preflight checks. See `preflight.txt`.
- PASS: canonical attestation, manual synchronization, and Module 05/10 native
  compilation with `-Wall -Wextra -Werror`; Module 10 compiled statically with
  libseccomp. See `integrity.txt`.
- PASS: capstone independent batch reference, two resource profiles, ordered
  success/failure/success, invalid batches, and empty transient-unit state.
  The starter and unmodified Module 10 solution were rejected.
- PASS: offline evidence classifications, a replay bundle moved to a separate
  directory, and bundle SHA-256 inventory checks.
- PASS: actual Lesson 12.02/12.03 student-workspace commands, missing-scenario
  deliberate failure, restored-scenario repair, deterministic packaging, reset,
  and final empty student/fixture/runtime directories. See `guided-replay.txt`.
- PASS: plain-mode `limactl copy` exported the evidence archive through SSH.
- PASS: deliberately withholding the deployment-evidence archive caused
  `limactl start --timeout=30s` to return 1, with no ready event. An initial
  unbounded readiness wait was stopped before this bounded negative check.
- PASS: after restoring the archive, a fresh stop/start returned ready. The
  archive SHA-256 remained
  `c77176a9b651be2af039fac0f2dd7d4abda0fdc424a04cf1f464c3dd8cf09648`
  and marker SHA-256 remained
  `c1418da40c98146ff22f6860e5ee5f4a2ef4f0f67ff66a3e5a0b6cde30a66410`.
  The marker-gated provision did not reinstall or re-extract.
- PASS: macOS control-plane run: 62 tests, 15 explicitly Linux-only skips,
  no failures. This is not Linux-kernel evidence.
- PASS: manual renderer produced a 172-page candidate PDF. Representative
  diagnostic, table, evidence lesson, code-wrapping, and capstone pages were
  visually inspected; all-page extracted text bounds found no overflow.
  Source directives do not appear as prose. This is a local candidate artifact,
  not a replacement for the published v1.0.2 PDF.
- PASS: `git diff --check`, course-manifest diff review, and source/manual sync.

## Limits

Fresh x86-64 CI was not run for this working tree. Debian and newer Landlock
ABI branches are not validated by this ABI 4 guest. The entire historical set
of guided lessons was not manually repeated; changed interfaces and automated
reference paths were exercised. No human learner pilot occurred. Follow the
pilot protocol separately and do not infer efficacy from automated passes.

Only synthetic local fixtures and services were used. No real credentials,
public/production target, host mount, or retained student solution was used.
The disposable validation VM is removed after evidence export; no user-owned
pre-existing VM was changed.
