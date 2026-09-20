# Fedora installer acceptance against published v1.0.2

This is a bootstrap acceptance run, not validation of the rewritten beta.
Run on 2026-09-19 in a new plain-mode Lima 2.2.0 ARM64 instance, with
4 CPUs, 6 GiB RAM, a 30 GiB disk, no host mounts, and no SSH-agent forwarding.
The existing learner Ubuntu VM was not modified.

Image: Fedora-Cloud-Base-Generic-44-1.7.aarch64.qcow2, pinned at
`https://download.fedoraproject.org/pub/fedora/linux/releases/44/Cloud/aarch64/images/Fedora-Cloud-Base-Generic-44-1.7.aarch64.qcow2`.
Image SHA256: `55c60a3b80d3616a08705afd0459e75fe9f03c54aba7a46e4002a41a72fa0d5b`.
Running kernel: `6.19.10-300.fc44.aarch64`; SELinux remained enforcing.
The ordinary user's unconfined SELinux domain is not a per-lesson confinement claim.
Package versions are recorded separately; a pinned image does not freeze packages
installed from the distribution repositories afterward.

## Observed results

- Clean install downloaded the published v1.0.2 archive and verified only its
  exact checksum entry. Archive SHA256:
  `52befb830193a152797272c0a6dcb0604c599c6f9aa8b1501819bc139f9f3233`.
- Published-release suite: 44 tests passed, zero skips, 7.359 seconds.
- Published-release preflight: 28 required checks passed, zero failed.
  These are the older release's counts, not the rewritten candidate's counts.
- Course attestation, manual synchronization, and warning-clean canonical
  Landlock compilation passed; managed runtime directories were empty afterward.
- Prepared lesson 01.01, then stopped and restarted normally. Its source SHA256
  remained `ff97b0a1d03d33e284bf7286d7caad4704caeeaf9f707ee513407396d00d2ba7`;
  readiness marker mtime remained `1789867847`. Provisioning did not overwrite
  the prepared work. Reset that owned test lesson and confirmed empty runtime.
- Replaced the readiness script in this disposable test instance with
  an unconditional failure. Start with a 45-second timeout returned exit 1.
  The VM remained booted: readiness failure is not a power-off operation.
  Explicitly stopped it, restored the actual readiness script, and started
  successfully again.
- Exported the deployment tarball through `limactl copy` from plain mode.
  Guest and host SHA256 both matched:
  `a3a56de7d665553c118cdc10607d940eccbdeaaf210752eadede52120f7e49f0`.
  Reviewed text records are retained here; the compiled smoke-test binary is not.

The beta must repeat candidate validation and then a clean actual-release
installation. This run proves the installer can bootstrap an available tagged
release; it cannot prove a future archive exists or installs correctly.
