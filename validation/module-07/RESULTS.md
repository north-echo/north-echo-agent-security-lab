# Module 07 Linux acceptance record

- Environment: Ubuntu 24.04.4 LTS arm64, kernel 6.8.0-134-generic, systemd 255, ordinary `lima` user
- Scope: three guided lessons, independent lab, practice/exam grading, replay, reset, transient-unit ownership, tests, and attestation

## Result

Module 07 passed its acceptance run.

- Lesson 07.01 observed an unlimited baseline and effective `CPUQuota=50%` as `cpu.max` value `50000 100000`.
- Lesson 07.02 completed a 16 MiB baseline and contained a synthetic 96 MiB allocator below `MemoryMax=33554432` with swap disabled.
- Lesson 07.03 bounded a request for 64 children with `TasksMax=12`, observed the effective limit and a PID maximum event, and collected the transient cgroup.
- The starter failed effective limits, PID pressure, and invalid-limit denial in practice and exam modes.
- A completed runner passed all 7 behavioral properties in both modes, including argv preservation, failure propagation, bounds validation, and post-run unit collection.
- Fresh grading details and unit names were used. Replay rotated the fixture and removed the completed solution.
- Module and `--all` reset paths removed all workspaces and fixtures. No matching user unit, process tree, cgroup, or managed artifact remained.
- The cleanup foundation separately proved exact name, description, delegated path, dry-run, stop, cgroup removal, and hostile ownership rejection.

## Boundaries

These exercises use the ordinary user's delegated systemd manager. CPU quota is not a latency guarantee; memory OOM outcome includes interpreter overhead; PID limits do not constrain CPU or memory. Network and credential policy remain separate layers.

All Module 07 acceptance items pass. Tranche 2 remains incomplete until Modules 08 and 09 pass their gates.
