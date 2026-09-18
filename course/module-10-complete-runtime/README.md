# Module 10 - Compose a complete agent runtime

Assemble the controls from Modules 01-09 in dependency order, then ask the running workload and kernel for evidence that the composition is effective. The final runtime has bounded resources, fresh user and network namespaces, empty capability sets, `no_new_privs`, Landlock filesystem policy, a default-deny seccomp filter, capability-mediated Unix-socket access, a clean credential environment, structured telemetry, and synchronous process-tree collection.

Play in order: `10.01`, `10.02`, `10.03`, then `module-10`.

Outcomes:

- distinguish launch dependencies from an arbitrary checklist order;
- apply pathname policy before a syscall filter can remove the setup syscalls;
- keep the broker outside the restricted network namespace while exposing only its Unix socket;
- place the launcher and every descendant under cgroup limits before workload creation;
- attest effective namespaces, capabilities, Landlock effects, seccomp mode, cgroup values, credential absence, and broker success;
- propagate workload failure and synchronously collect the exact transient unit.

All data, credentials, capabilities, services, paths, and requests are synthetic and local. The module creates no veth pair, route, firewall rule, public request, real credential, or production target. Prerequisites are Modules 01-09 and the Linux features reported by `./scripts/linux-preflight`.
