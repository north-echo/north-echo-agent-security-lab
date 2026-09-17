# Roadmap to the complete course

v0.1 proves the lifecycle and completes the first three foundations. The remaining course will be built in gated tranches. A tranche is not complete until every included module passes `docs/MODULE_ACCEPTANCE_TEMPLATE.md`, the field manual is synchronized, and the behavior has been exercised on the disposable Linux VM.

## Gate A - Linux baseline for v0.1

**Status: complete on Ubuntu 24.04.4 LTS arm64.** The full record is in `validation/RESULTS.md`. Debian 12 and x86-64 remain additional baselines rather than prerequisites for starting Tranche 1.

- Run `docs/LINUX_VALIDATION.md` for all nine guided lessons and three independent labs.
- Exercise practice and exam grading, randomized replay, every reset scope, integrity rejection, and cleanup containment.
- Fix Linux portability defects with regression tests.
- Record the exact distribution, kernel, architecture, tool versions, results, skips, and residual risks.

Do not begin Module 04 until this gate is complete.

## Tranche 1 / v0.2 - Modules 04-06

**Status: complete on Ubuntu 24.04.4 LTS arm64.** Modules 04-06 passed their module gates and the end-to-end tranche record is in `validation/tranche-01/RESULTS.md`. Module 07 is next.

- Module 04: local deterministic tool-using agent, structured tool calls, full action trace, intentionally ambient authority.
- Module 05: traversal and symlink failures, `openat2` resolution, descriptor-relative policy, Landlock ABI detection, pre-opened-FD variant.
- Module 06: measured syscall profiles, seccomp filter construction, errno vs kill observation, alternate-syscall bypass, composition limits.

Add grader isolation so evaluation probes run from a read-only copy and record kernel/config prerequisites in status output. Gate the tranche with end-to-end replay, safe teardown, complete manual chapters, and Linux evidence for every module.

## Tranche 2 / v0.3 - Modules 07-09

**Progress:** Module 07's fail-closed transient-user-unit registry and delegated-cgroup cleanup foundation is implemented and Linux-exercised. Guided lessons, lab, grader, manual chapter, and full module acceptance remain in progress.

- Module 07: cgroup v2 CPU, memory, and PID limits with pressure/OOM observations and delegated-subtree cleanup.
- Module 08: network namespace, synthetic local services, direct-egress denial, mediated broker, DNS and redirect reauthorization.
- Module 09: fake credential exposure, operation broker, audience/run binding, expiry, replay cache, confused-deputy variants.

Extend the runtime registry to network links, nftables state, service PIDs, and delegated cgroups with dry-run verification and hostile-registry tests before lessons create those resources. Gate the tranche with complete manual chapters and proof that teardown leaves no owned resource behind.

## Tranche 3 / v0.4 - Modules 10-12

- Module 10: assemble all controls in a security-correct launch order and emit an attestation of effective state.
- Module 11: randomized deliberately vulnerable variants, reference probes, invariant identification, repair, hardened counterpart.
- Module 12: bounded adaptive agent, scripted baseline comparison, calibrated interpretation, Boundary Atlas experiment package.

Gate the tranche with cross-layer bypass tests, complete manual chapters, and a full-course clean replay from a fresh VM snapshot.

## Gate D / v1.0 - Cold capstone

`./lab-start capstone --cold` creates a fresh unlabeled runtime objective, randomized synthetic services/data, no guided references in the workspace, and a multi-layer external grader. Reset removes every student artifact but preserves attempt/pass metadata. Capstone variants must be independently solvable from skills already practiced and must never require a production credential or external target.

Release v1.0 only with a reproducible source archive, Git history bundle, checksums, release notes, full Markdown field manual, visually checked PDF manual, and supported-Linux validation records.
