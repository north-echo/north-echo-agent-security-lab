# Audit implementation — 2026-09-19

Baseline: `fa267ef4d3c5b265704b615232a4006d9d0f6a2d` (v1.0.2 plus final deployment record).

Implementation follows the audit order. This record distinguishes implementation
from Linux validation and human learner evidence; neither is inferred from unit tests.

1. Cleanup ownership, validation before mutation, and confirmed termination.
2. Behavioral, module-specific readiness and strict Linux test coverage.
3. Module 10 Landlock policy and teaching consistency.
4. Grader deadlines, result validation, diagnostics, and exception cleanup.
5. Complete onboarding using the shared package manifest.
6. A distinct transfer-oriented capstone.
7. Offline evidence interpretation, observed action accounting, and replay packaging.
8. Canonical source/manual synchronization and stale completion claims.
9. Current versus historical achievement and serialized lifecycle transactions.
10. Entry diagnostic, fading scaffolds, cumulative checkpoints, and learner pilot protocol.
11. Test-copy efficiency, readable graders, release metadata, package inventory.

Status: implementation complete in the working tree; not tagged or published.
`VERSION` remains the existing release identifier until a new release is approved.
The default appliance still installs published v1.0.2, not this working tree.

## Implementation and regression coverage

| Order | Delivered change | Evidence |
| --- | --- | --- |
| 1 | Whole-scope cleanup planning, target-specific mounts, fail-closed systemd inspection, PID identity/pidfd exit confirmation, safe registry writes | Cleanup planning, delegated-unit, hostile-path, and symlink tests |
| 2 | Actual openat2/Landlock/seccomp enforcement and effective cgroup resource checks; Linux CI rejects skipped tests | 33 preflight checks; strict suite passes with zero skips |
| 3 | Module 10 handles build-known/runtime-supported filesystem rights consistently with Module 05; observability exceptions are explicit | Strict native compilation and full composition tests |
| 4 | Shared execution deadlines/output limits, malformed-result failure checks, exact-process exception cleanup, bounded service reads | Shared runtime tests and all module regressions |
| 5 | Complete clone/install/enter-lesson instructions, shared package manifest, scoped guest setup, separate private work export | Fresh pinned appliance boot and guided workspace runs |
| 6 | Ordered-batch capstone with multiple resource profiles, continuation after job failure, invalid-input rejection, distinct units, and human rationale rubric | Independent batch reference passes; starter and unchanged Module 10 implementation do not |
| 7 | Independent oracle-call accounting, offline complete/incomplete/ambiguous evidence comparison, source/input/hash replay bundle | Unreported-call regression; relocated replay; guided missing-input failure and repair |
| 8 | Canonical source includes regenerate listings and assembled manual; CI detects drift | Source-change regression and manual check; PDF renderer also fixes tables, continuation bullets, excess page breaks, and long-code clipping |
| 9 | Latest result, attempt, mode and failed properties separated from historical achievement; locked lifecycle transactions | Failed-regrade and multiprocess update tests |
| 10 | Entry diagnostic, per-module fading, cumulative 03/06/09 checkpoints, graduation rubric, and learner-pilot protocol | Materials included in the manual; actual participant evidence intentionally pending |
| 11 | Test copies exclude Git/build artifacts; later graders and tests are readable; authoritative VERSION; installed package revisions exported | Metadata consistency tests; packages.tsv from fresh deployment |

## Validation and limits

See [the retained validation record](../../validation/audit-20260919/RESULTS.md).
Ubuntu 24.04.5 arm64, kernel 6.8.0-139-generic: 62 tests passed with no skips;
all 33 required preflight checks passed. macOS: 62 tests ran, 15 expected
Linux-only skips, no failures. Attestation, manual synchronization, strict native
compilation, and diff whitespace checks passed. The PDF was rebuilt and sampled
visually, with all-page text-bound checks.

Fresh x86-64 CI is still required before publishing this candidate; historical
x86-64 release evidence is not reused as proof. Debian remains unvalidated.
Newer Landlock ABI branches are header/kernel gated and were not runtime-tested
on this ABI 4 guest. Human pilot results require actual participants; the
implemented deliverable is an executable study protocol and recording template,
not generated learner feedback. No efficacy or completion-time claim is made.
