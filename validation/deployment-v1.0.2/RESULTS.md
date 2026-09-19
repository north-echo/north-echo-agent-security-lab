# v1.0.2 Lima deployment validation

## Decision

**PASS** — the pre-release mechanics run passed on commit `16e69e4b4be4dd3d6f8cd976d76359ec32b2a34f`, and the final release gate passed against the published `v1.0.2` assets from tagged commit `036c8e6376102a7dd5b0066ed77fe903429cea06`. The final run used the template's default `CourseVersion: v1.0.2`; no override, host mount, production credential, or external target was used.

## Host and guest baseline

- Host: macOS on arm64; Lima 2.2.0 using Apple's Virtualization framework (`vz`)
- Template: `deploy/north-echo.yaml`, `plain: true`, 4 CPUs, 6 GiB memory, 30 GiB disk
- Host integration disabled: filesystem mounts, dynamic port forwarding, built-in containerd, guest agent, Rosetta, and SSH-agent forwarding
- Image: Ubuntu cloud image release `noble/release-20260911`, arm64 SHA-256 `7b682958a67ff5de068e36de6af8b75fa645d296af5a70d6500527f6a33781db`
- Guest: Ubuntu 24.04.5 LTS arm64, kernel `6.8.0-139-generic`, ordinary `lima` user (UID 501)
- Course archives: `v1.0.1` for the pre-release mechanics run and the default `v1.0.2` for the final release gate

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

## Final release gate

- GitHub published `v1.0.2` with the Markdown and PDF manuals, release notes, `SHA256SUMS`, source archive, and Git bundle. The tag-triggered Ubuntu 24.04 workflows passed on x86-64 and arm64.
- A new `north-echo-v102-final` instance selected the pinned arm64 image and downloaded the release through the template's unmodified `CourseVersion: v1.0.2` path.
- The guest reported Ubuntu 24.04.5 LTS arm64 with kernel `6.8.0-139-generic`, and the installed root marker reported `North Echo Agent Security Lab v1.0.2`.
- All 44 Linux tests passed in 5.979 seconds, all 28 required preflight checks passed, course attestation passed, the strict Module 05 Landlock compile artifact was present, `Linger=yes`, and managed runtime state was empty.
- The final readiness marker recorded `course_version=v1.0.2`, image release `20260911`, and ready time `2026-09-19T03:24:50Z`.
- Plain-mode `limactl copy` exported the archive through the guest's resolved home path, `/home/lima.guest/north-echo-deployment-evidence.tgz`. The local archive SHA-256 was `30f783a74b78daa46753486591784b1a4dbbb14a18c76790d3a1a09ba12ff136`, and it contained only the expected environment, tests, attestation, preflight, empty-runtime, and Landlock compile artifacts.
- A synthetic student-work marker survived stop/start. The readiness marker retained SHA-256 `e0c0cdabc10b32c4dae47b2663fe853636c56957a1f83f87828b00d4c9c6f33c` and modification time `1789788290`; the restart returned ready in 7.8 seconds without reinstalling or re-extracting.
- The synthetic marker was removed, the managed directories were confirmed empty again, the instance was deleted, and `limactl list` reported no remaining instances.

The v1.0.2 deployment gate is complete.
