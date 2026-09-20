# Resource-control rewrite candidate: Fedora regression gate

Candidate archive SHA256:
`73d80675a132f082b93b222f1c91acf49dd5224c9706a890a859c075e97a632a`.
This is an intermediate uncommitted candidate, not a release archive.

Fedora 44 ARM64, kernel `6.19.10-300.fc44.aarch64`, systemd 259.5:

- Strict suite: 99 tests passed without skips, 18.599 seconds.
- Course attestation and manual synchronization: PASS.
- Linux preflight: 33 required checks passed, zero failed; Landlock ABI 7.

The three added guided tests prepare real lesson workspaces and execute the
actual fenced commands from the revised READMEs. They observe the CPU quota,
the memory ceiling plus specific `oom-kill` result, task creation plus a positive
controller event, and a client timeout followed by registered ownership-checked
cleanup. Invalid allocator/task counts are rejected before creating pressure.

A fourth regression demonstrates that systemd's default argument expansion
changes a supplied `${NAME}` literal. The repaired reference explicitly uses
`--expand-environment=no`; the Module 07 grader now checks this case. The task
grader also requires a positive PID-limit event rather than mere presence of an
event-field name. Its bounded reference supplies a service runtime backstop and
verifies the unit description/delegated cgroup before a timeout stop.

The installed systemd manuals were read for collection, waiting, argument
expansion, CPU quota period, memory/swap, and task-limit semantics. Online
freedesktop manual pages returned HTTP 403; the installed manuals were the
primary source for the baseline-specific review.

All pressure remained inside fixed-size synthetic test workloads and delegated
user units. This gate does not establish human comprehension, exhaust every
service-manager race, or validate the later rewrite. Final beta and actual
published-artifact installation gates remain outstanding.
