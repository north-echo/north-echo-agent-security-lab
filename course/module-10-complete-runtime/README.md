# Module 10 - Compose a complete agent runtime

Assemble the controls from Modules 01-09 in dependency order, then ask a known workload and kernel for evidence of their combined effects. This instrumented teaching runtime has bounded workload resources, fresh user/network namespaces, reduced capabilities, `no_new_privs`, Landlock filesystem policy, default-deny seccomp, an intended capability-mediated Unix-socket exchange, a fixed workload environment, and exact owned-unit collection checks. It is not a production general-purpose agent sandbox.

Play in order: `10.01`, `10.02`, `10.03`, then `module-10`.

Outcomes:

- distinguish launch dependencies from an arbitrary checklist order;
- apply pathname policy before a syscall filter can remove the setup syscalls;
- keep the broker outside the restricted network namespace while demonstrating the intended pathname Unix-socket operation;
- place the launcher and every descendant under cgroup limits before workload creation;
- attest effective namespaces, capabilities, Landlock effects, seccomp mode, cgroup values, credential absence, and broker success;
- propagate workload failure and synchronously collect the exact transient unit.

All data, credentials, capabilities, services, paths, and requests are synthetic and local. The module creates no veth pair, route, firewall rule, public request, real credential, or production target. Prerequisites are Modules 01-09 and the Linux features reported by `./scripts/linux-preflight`.

## Learning route and limits

First validate a dependency plan without claiming it installed controls. Next
compare a native observer before and after the inner guard. Finally compose the
outer layers and compare separate evidence for workload effects, synthetic
broker use, and exact unit/socket teardown. A small static worker bridges to
ordered batch practice without supplying a capstone implementation.

This design does not create private PID/mount views. It permits selected
read-only observations and, on the validated Landlock ABI 7 kernel, does not
enforce ABI 9 pathname Unix-socket-resolution restrictions. Do not claim the
intended broker is the only reachable Unix socket. The tiny opaque-token broker
is a composition fixture, not the full Module 09 authorization protocol.

An attestation here is a local report from known teaching code, not cryptographic
remote attestation or proof that arbitrary workload code tells the truth.
Launcher output capture is not independently byte-bounded. Keep the exercises
small, synthetic, and inside the disposable VM; preserve SELinux enforcement.
