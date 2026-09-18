# Module 10 acceptance record

Status: **PASS** on Ubuntu 24.04.4 LTS arm64 with Linux 6.8.0-134-generic.

Source under test: Module 10 feature branch based on `bc4e782`; the final commit hash will be the commit containing this record. Date: 2026-09-17.

## Acceptance checklist

- [x] Three substantive guided lessons with exact commands, complete guided source listings, local explanations, expected observations, intentional failures, repairs, checkpoints, and troubleshooting.
- [x] Independent lab specifies the composition interface and properties without shipping a completed lab implementation.
- [x] `10.01`, `10.02`, `10.03`, and `10.lab` start through the public lifecycle CLI with fresh synthetic fixtures.
- [x] Launch dependencies require cgroup, namespaces, privilege floor, Landlock, seccomp, workload execution, and collection in security-correct order.
- [x] External grader compiles trusted static native probes and evaluates a read-only student launcher copy with fresh paths, capability, fake credential, canary, broker, and unit identity.
- [x] Runnable starter exercises the inner guard but fails composition; completed implementation passes all 11 properties in practice and exam modes.
- [x] Effective-state attestation proves exact cgroup limits, private user/network namespaces, direct-IP denial, empty capabilities, `no_new_privs`, seccomp mode, allowed read, and protected-path denial.
- [x] A host-side Unix-socket broker uses its fake credential for one capability-bound operation without placing the credential in workload environment, argv, result, or output.
- [x] Literal paths avoid shell evaluation; invalid roots and unbounded limits fail before unit/result creation; workload status and stderr propagate.
- [x] Transient cgroup service is synchronously collected on success and failure. Timeout targets only the exact random unit.
- [x] Lesson, module dry-run, module reset, and replay lifecycle paths pass with fresh fixture rotation.
- [x] No persistent resource is created; foreground broker socket and transient service leave no owned object behind, so registry expansion is unnecessary.
- [x] Full field-manual chapter contains the synchronized guided commands, complete sources, security model, lab contract, and troubleshooting.
- [x] Full automated suite passes 35/35 on Linux; course attestation and 28-check Linux preflight pass.

## Evidence

- `environment.txt`: distribution, kernel, architecture, and relevant tool versions.
- `tests.txt`: full automated result, attestation, and preflight summary.
- `lessons.txt`: all three guided paths and effective observations.
- `grading.txt`: starter failure plus completed practice/exam results.
- `lifecycle.txt`: start, reset, fixture rotation, and cleanup paths.
- `final.txt`: empty workspaces, sockets, services, and temporary lesson objects.

## Safety and residual risk

Only synthetic local files, capabilities, credentials, Unix sockets, and operations were used in the disposable VM. No real credential, public request, DNS query, LAN host, cloud metadata endpoint, employer system, host firewall change, veth device, privileged cgroup, or production resource was involved. No feature was skipped.

The runtime is educational rather than a production sandbox. Its trusted guard and static probe have a deliberately small fixed policy; Landlock does not revoke already-open descriptors; the broker capability is a local bearer value; and the attestation is returned by the contained workload rather than signed by a remote verifier. The platform checks honest work and is not a hostile multi-user boundary. These limits do not weaken the launch-order, effective-state, mediated-operation, failure-propagation, or teardown objectives.
