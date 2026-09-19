# v1.0.2 Lima deployment validation

## Decision

**CONDITIONAL PASS** — commit `16e69e4b4be4dd3d6f8cd976d76359ec32b2a34f` passed template validation and the complete plain-mode appliance acceptance path on Apple Silicon. The run overrode `CourseVersion` to the already published `v1.0.1` release so it could exercise real release download and checksum verification before a `v1.0.2` release exists. The final v1.0.2 release gate must repeat the fresh-create and copy-out checks without that override against the published v1.0.2 assets.

## Host and guest baseline

- Host: macOS on arm64; Lima 2.2.0 using Apple's Virtualization framework (`vz`)
- Template: `deploy/north-echo.yaml`, `plain: true`, 4 CPUs, 6 GiB memory, 30 GiB disk
- Host integration disabled: filesystem mounts, dynamic port forwarding, built-in containerd, guest agent, Rosetta, and SSH-agent forwarding
- Image: Ubuntu cloud image release `noble/release-20260911`, arm64 SHA-256 `7b682958a67ff5de068e36de6af8b75fa645d296af5a70d6500527f6a33781db`
- Guest: Ubuntu 24.04.5 LTS arm64, kernel `6.8.0-139-generic`, ordinary `lima` user (UID 501)
- Course archive used for this pre-release mechanics run: `v1.0.1`

The installed package baseline was AppArmor 4.0.1, build-essential 12.10, curl 8.5.0, iproute2 6.1.0, libcap 2.66, libseccomp 2.5.5, Linux userspace headers 6.8.0-139, pkgconf 1.8.1, procps 4.0.4, Python 3.12.3, strace 6.8, and util-linux 2.39.3. Exact Debian revisions were captured during the run.

## Results

- `limactl validate deploy/north-echo.yaml` passed with Lima 2.2.0.
- Lima selected the pinned arm64 image and its configured digest.
- The resolved instance configuration retained `plain: true`, an empty mounts list, disabled containerd, `forwardAgent: false`, and `loadDotSSHPubKeys: false`.
- The data provision copied `deploy/ubuntu-packages.txt`; both the system provision and GitHub Actions consume that shared manifest.
- The first boot installed prerequisites, enabled lingering for `lima`, and proved `systemctl --user` plus a transient `systemd-run --user` unit. `loginctl show-user lima -p Linger` reported `Linger=yes`.
- The release archive's single matching line from `SHA256SUMS` verified before extraction.
- All 42 Linux tests passed in 6.512 seconds, course attestation passed, all 28 required preflight checks passed, the Module 05 launcher compiled with `-Wall -Wextra -Werror`, and managed runtime state was empty.
- The generated readiness marker SHA-256 was `afc6541a1468d2522f8e18bdcf73cdda69ea1750abb577972a1ee1f9f9b2f49a`.
- A synthetic student-work file survived stop/start. The readiness marker's SHA-256 and modification time were unchanged, and the restart reached ready state in under ten seconds without reinstalling or re-extracting.
- `limactl copy` exported the evidence archive from the plain-mode instance. Its SHA-256 was `853eb2093bb6ad129c85cbf9caf81c3d5b292ca1acafbb483364b3e51cbeea96`; inspection found only environment, tests, attestation, preflight, empty-runtime, and Landlock compile artifacts.
- A temporary copy of the template replaced the readiness probe with `exit 1`. `limactl start --timeout=30s` returned exit status 1 and never reported the instance ready. The negative-test instance was then deleted.
- The synthetic restart marker was removed after the check. No student solution, real credential, external target, or host filesystem mount was used.

## Remaining release gate

Publish the v1.0.2 archive and `SHA256SUMS`, create a fresh instance with the template's default `CourseVersion: v1.0.2`, repeat the first-boot validation and plain-mode `limactl copy`, record the final tag commit, and delete the instance. Until then, the deployment implementation is validated but the not-yet-published default artifact chain is necessarily pending.
