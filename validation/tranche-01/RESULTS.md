# Tranche 1 / v0.2 Linux gate

Tranche 1 passed on Ubuntu 24.04.4 LTS arm64, kernel 6.8.0-134-generic.

- Modules 04, 05, and 06 each contain three guided lessons, one independent lab, a synchronized manual chapter, behavioral grading, randomized replay, and Linux evidence.
- The final suite contains 22 passing tests with no Linux skips; course attestation passes and the expanded playable-module preflight reports 23/23 required checks passing.
- Module 04 evaluation copies the Python submission read-only; Modules 05-06 compile read-only source copies and run fresh external probes.
- `lab-status` records the Linux/kernel/tooling prerequisites for filesystem and seccomp modules.
- Practice/exam grading, replay rotation, lesson/module/`--all` reset, pass-metadata retention, and empty managed directories were exercised across the tranche.
- No retained student solution, real credential, external target, background process, mount, cgroup, service, or network object remains.

Tranche 2 may begin with Module 07. Before any cgroup or network lesson creates a persistent resource, extend the ownership registry and adversarial cleanup tests for that resource type.
