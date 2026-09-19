# Module 05 Linux acceptance record

- Source: checkpoint `08d1712` plus the working-tree changes through Module 05
- Environment: Ubuntu 24.04.4 LTS arm64, kernel 6.8.0-134-generic, Python 3.12.3, GCC 13.3.0, Landlock ABI 4, ordinary `lima` user
- Scope: three guided lessons, independent lab, practice/exam grading, replay, all reset scopes, cleanup, tests, and course attestation

## Result

Module 05 passed its acceptance run.

- Lesson 05.01 reproduced prefix-collision traversal and symlink escape against lexical validation, then denied both using resolved component containment while explicitly retaining the check/use caveat.
- Lesson 05.02 preserved an allowed read and denied traversal and symlink lookup with descriptor-relative `openat2`. Removing the confinement flags reproduced both escapes; restoring them passed the checkpoint.
- Lesson 05.03 detected the Landlock ABI, preserved execution and allowed access, denied a child's new outside open, and denied use of a deliberately inherited protected descriptor. Removing inherited-descriptor cleanup reproduced that distinct bypass; restoring it denied the read.
- The untouched lab starter preserved basic reads, writes, and child execution but failed traversal, symlink, Landlock, and inherited-descriptor properties in both practice and exam modes.
- A completed solution passed all 9 behavioral properties in both practice and exam modes.
- A fresh evaluation fixture was generated for every grade. Replay rotated the start fixture and removed the prior solution.
- Lesson, module, and `--all` dry-run/real reset paths were exercised. No owned runtime or temporary artifact remained; pass metadata was retained.
- The grader evaluates a read-only copy of the submission in a fresh temporary tree.
- No real credential, external API, external target, mount, or host policy change was used.

Raw command transcripts are stored beside this file. Host-specific repository paths and generated canaries are redacted before retention.

## v1.0.1 portability addendum — 2026-09-18

GitHub Actions run `35415279577` passed the complete course validation job on both supported Ubuntu 24.04 runner architectures:

- `ubuntu-24.04`: Ubuntu 24.04.5 LTS, kernel 6.17.0-1022-azure, `x86_64` / `amd64`
- `ubuntu-24.04-arm`: Ubuntu 24.04.5 LTS, kernel 6.17.0-1022-azure, `aarch64` / `arm64`

Each runner passed all 42 automated tests, course attestation, all 28 required Linux preflight checks, and the empty-runtime check. Each also compiled the canonical Lesson 05.03 Landlock launcher with `cc -std=c11 -Wall -Wextra -Werror -O2`. This directly validates that the source's ABI-gated filesystem rights compile cleanly against Ubuntu 24.04 userspace headers on both architectures. Runtime properties for rights introduced after the runners' supported/header-visible set remain documented rather than claimed as externally graded.

## Known boundaries

The lesson's resolved Python check demonstrates correct component comparison but is intentionally not presented as atomic authorization. `openat2` governs only brokered lookups. Landlock governs future filesystem operations but not I/O through pre-opened file descriptions, so descriptor hygiene remains a separate required layer. The static child probe keeps the lesson ruleset small; production dynamic programs would need deliberately selected read/execute rules for their runtime files.

## Acceptance disposition

All Module 05 requirements in `docs/dev/MODULE_ACCEPTANCE_TEMPLATE.md` are satisfied. Tranche 1 remains incomplete until Module 06 passes the same gate.
