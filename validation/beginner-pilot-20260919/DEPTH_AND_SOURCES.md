# Pilot depth/source revision acceptance

Date: 2026-09-19 (local review date). This follows the initial mechanical pilot
record in `RESULTS.md`; it does not retroactively change that record's revision.

## Candidate and baseline

- Uncommitted working copy based on `a6f62ce2f973fac4aa3604ee4abe82af136317b7`.
- Tested transfer archive SHA-256:
  `2aebedfb5ee82c26332128698166699167095e68b0a6ca1a1b04cdaac1db6f5a`.
- Course manifest SHA-256:
  `ca988948aaa23b19c6a538c21fe41baf197c4da63b19297fe096a61055ce63ce`.
- Ubuntu 24.04.5 LTS arm64; Linux 6.8.0-139-generic; Python 3.12.3;
  Bash 5.2.21; GNU coreutils 9.4; nano 7.2.
- Separate owned Lima validation VM, using the original pinned plain-mode
  appliance. A fresh candidate extraction was used; the user's `north-echo`
  instance and existing student work were not changed.

This snapshot contains the revised lessons, manuals, source review, and tests.
This result file and final handoff/README status notes were added afterward.
No lesson program or grader implementation changed in this revision.

## Results

```text
python3 scripts/run_tests.py --require-no-skips
Ran 76 tests in 14.255s
OK

./scripts/attest-course
COURSE ATTESTATION: PASS

python3 scripts/build_field_manual.py --check
FIELD_MANUAL.md is synchronized

./scripts/linux-preflight
SUMMARY: 33 required checks passed; 0 required checks failed
```

The new regression checks verify file-access commands before every guided Python
listing, execute the named `ls -l` / `cat` operations against supplied files,
retain per-lesson/practical source-and-scope sections, and demonstrate why text
reading does not guarantee binary newline preservation. Extended guided tests
exercise directory-as-file failure, presence of an empty environment value,
and the empty-environment worker's early exit without observer output.

A direct B0.02 shell walkthrough separately confirmed: preparation creates
`identify.py`; `pwd` identifies the lesson; `ls -l` finds the file; `cat` prints
the supplied source; the ordinary invocation followed by `echo $?` reports 0;
the `fail` invocation followed by `echo $?` reports 7. The two processes had
different IDs and the same launching parent in that run. Reset removed this
owned lesson. Final managed-directory inspection and `north-echo-*` user-unit
inspection were empty. No generated fixture values or student solutions are
retained here. Only synthetic local workers/data were used.

Host control-plane result: 76 tests discovered, 61 passed, 15 expected Linux
skips. Host preflight correctly rejected macOS. `git diff --check` passed.
The Linux extraction warned about two unsupported macOS extended-header keys;
these were ignored, and integrity, executable CLI checks, and tests passed.

## Source review and limits

`docs/dev/BEGINNER_SOURCE_REVIEW.md` maps substantive B0/B1 claims to inspected
primary sections and distinguishes documented behavior, course policy, and
observed results. It records documentation/runtime version differences and
the two narrowed claims: LF-text preservation and ordinary exit-code forwarding.

No new x86-64 run, interactive editor usability study, or human learning
assessment occurred. Source-link presence tests cannot prove relevance or
teaching quality. This is a reviewed pilot with mechanical evidence, not a
claim that the complete course now matches an established course's educational
depth. No commit, push, release, or new PDF was made in this revision.
