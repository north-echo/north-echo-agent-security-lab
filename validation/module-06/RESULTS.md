# Module 06 Linux acceptance record

- Source: checkpoint `08d1712` plus the working-tree changes through Module 06
- Environment: Ubuntu 24.04.4 LTS arm64, kernel 6.8.0-134-generic, Python 3.12.3, GCC 13.3.0, libseccomp 2.5.5, ordinary `lima` user
- Scope: three guided lessons, independent lab, practice/exam grading, replay, reset, tests, and course attestation

## Result

Module 06 passed its acceptance run.

- Lesson 06.01 measured a working file-copy path with `strace`, then showed that an empty input omits the data `write` observed for nonempty input.
- Lesson 06.02 observed `EPERM` continuation and `SIGSYS` process termination for the same denied socket syscall. A local `socketpair` bypassed the single-name blacklist.
- Lesson 06.03 proved `NoNewPrivs: 1` and `Seccomp: 2` inside the executed child. The stated file read succeeded; socket, socketpair, ptrace, and an unlisted harmless syscall returned `EPERM`. Temporarily allowing `getppid` reproduced over-authorization, and restoring the list denied it.
- The untouched lab starter preserved the file workload but failed all six confinement/effective-state properties in practice and exam modes.
- A completed solution passed all 9 behavioral properties in both modes.
- Every grade used a fresh external static probe and a read-only copy of the submission.
- Replay rotated the fixture and removed the completed solution. Module and `--all` dry-run/real resets were exercised; no managed artifact remained.
- No external network target, real credential, privilege escalation, or host security-policy change was used. Socket probes used only local AF_UNIX creation.

## Known boundaries

The allowlist is intentionally tied to the supported static teaching probe and current architecture. Dynamic applications need their own measured startup/error paths. Seccomp filters syscall interfaces and arguments; it does not authorize pathnames, meter resources, select network destinations, or revoke inherited descriptors. Those are separate layers.

## Acceptance disposition

All Module 06 requirements in `docs/dev/MODULE_ACCEPTANCE_TEMPLATE.md` are satisfied.
