# Roadmap

v0.1 proves the lifecycle and completes the first three foundations. Expansion should preserve the same replay, grading, safety, and teaching contracts.

## v0.2 - Modules 04-06

- Module 04: local deterministic tool-using agent, structured tool calls, full action trace, intentionally ambient authority.
- Module 05: traversal and symlink failures, `openat2` resolution, descriptor-relative policy, Landlock ABI detection, pre-opened-FD variant.
- Module 06: measured syscall profiles, seccomp filter construction, errno vs kill observation, alternate-syscall bypass, composition limits.

Add grader isolation so evaluation probes run from a read-only copy and record kernel/config prerequisites in status output.

## v0.3 - Modules 07-09

- Module 07: cgroup v2 CPU, memory, and PID limits with pressure/OOM observations and delegated-subtree cleanup.
- Module 08: network namespace, synthetic local services, direct-egress denial, mediated broker, DNS and redirect reauthorization.
- Module 09: fake credential exposure, operation broker, audience/run binding, expiry, replay cache, confused-deputy variants.

Extend the runtime registry to network links, nftables state, service PIDs, and delegated cgroups with dry-run verification tests.

## v0.4 - Modules 10-12

- Module 10: assemble all controls in a security-correct launch order and emit an attestation of effective state.
- Module 11: randomized deliberately vulnerable variants, reference probes, invariant identification, repair, hardened counterpart.
- Module 12: bounded adaptive agent, scripted baseline comparison, calibrated interpretation, Boundary Atlas experiment package.

## v1.0 - Cold capstone

`./lab-start capstone --cold` creates a fresh unlabeled runtime objective, randomized synthetic services/data, no guided references in the workspace, and a multi-layer external grader. Reset removes every student artifact but preserves attempt/pass metadata. Capstone variants must be independently solvable from skills already practiced and must never require a production credential or external target.
