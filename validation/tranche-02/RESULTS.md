# Tranche 2 / v0.3 acceptance record

Status: **PASS** on Ubuntu 24.04.4 LTS arm64 with Linux 6.8.0-134-generic. Date: 2026-09-17.

Scope: Modules 07-09—delegated cgroup v2 controls, empty-network-namespace mediated egress, and fake-credential capability brokering.

## Gate results

- [x] Module 07 acceptance record passes CPU, memory, PID, transient-unit ownership, and subtree cleanup properties.
- [x] Module 08 acceptance record passes direct-IP denial, Unix-socket mediation, destination/run binding, and redirect reauthorization.
- [x] Module 09 acceptance record passes ambient-credential repair, signed capability binding, upstream credential use, replay, lifetime, secret-file mode, non-disclosure, and confused-deputy properties.
- [x] Complete Markdown manual chapters exist and are synchronized for Modules 07, 08, and 09.
- [x] Full automated suite passes 33/33 with no skips on Ubuntu arm64.
- [x] Course attestation passes and Linux preflight reports 28 required checks passed, 0 failed.
- [x] Fresh `07.lab`, `08.lab`, and `09.lab` workspaces and fixtures were created through the public CLI.
- [x] All-scope reset dry-run named only the three fresh workspace/fixture pairs and changed no state.
- [x] All-scope reset removed all three pairs while retaining attempt/pass metadata.
- [x] Final managed-tree, socket, helper-process, and temporary-directory inspection was empty.

## Cleanup model

Module 07 registers narrowly named transient user units and proves exact description plus delegated cgroup ownership before systemd cleanup. Module 08 creates only process-lifetime network namespaces, exact-PID synthetic services, and workspace sockets. Module 09 likewise uses exact-PID broker/upstream processes and workspace sockets/files. No veth, route, firewall, DNS, persistent credential service, key store, or replay database exists.

## Safety and residual risk

The tranche used only bounded synthetic workloads, loopback or filesystem-socket services, and fake credentials. It touched no LAN, public, cloud metadata, employer, or production target. No completed student solution, generated canary, capability, signing key, or fake credential was retained.

Additional supported baselines remain future validation work; this gate proves Ubuntu 24.04.4 LTS arm64 and the GitHub Actions Ubuntu x86-64 control/kernel matrix once the merge workflow passes.
