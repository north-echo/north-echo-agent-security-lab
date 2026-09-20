# Disposable Linux VM setup

## Choose the baseline

For this learner-review beta, **Fedora 44 ARM64 on Apple Silicon** is the preferred new-install path. The image is pinned, SELinux remains enforcing, and the course runs as an ordinary user. Fedora x86-64 is not covered by this template or inferred from ARM64 results.

Ubuntu 24.04 remains a compatibility path with a separate pinned template and x86-64/ARM64 CI. Read the release's validation record for the exact revision tested; old release evidence does not validate new code. Debian and other distributions are not acceptance baselines.

Desktop versus Server is not the deciding feature. A real booted Linux kernel, user systemd manager, delegated cgroup v2 controllers, user/network namespaces, working Landlock/seccomp, and the required toolchain are. A minimal cloud/server image avoids unnecessary desktop components. A container on macOS is not this guest environment.

Use 4 CPUs, 6 GiB memory, and 30 GiB disk. No real credentials, production data, shared host directory, SSH-agent forwarding, or public service is needed.

## Create a separate beta VM on your Mac

Install Lima 2.2 or newer using its official installation instructions, then check `limactl --version`. These are **Mac host** commands. Choose a new name; do not reuse or delete your existing `north-echo` learner VM.

```bash
git clone --branch v2.0.0-beta.1 --depth 1 https://github.com/north-echo/north-echo-agent-security-lab.git north-echo-beta-source
cd north-echo-beta-source
limactl start --name north-echo-beta deploy/north-echo-fedora.yaml
limactl shell north-echo-beta
```

The tagged checkout contains the template and its companion package list. Run the start command from that checkout. Fedora installation downloads the pinned image and release; first boot takes longer than a restart. Successful readiness is required before beginning.

The last command opens the **Linux guest** shell. Now, inside it:

```bash
cd ~/north-echo
pwd
./scripts/linux-preflight
./scripts/attest-course
./lab-start b0.01
cd .student/b0.01
less README.md
```

The installer places the course under the guest user's home, not in a host mount. Preflight checks actual prerequisites; attestation checks canonical file integrity. `lab-start` prepares a student copy. `less` reads instructions; press q to exit. Do not type Linux exercise commands into your Mac shell.

If you already know the B0 material, return to the guest course root and try `./lab-start module-b0`; its directory is `.student/b0.lab`, not `.student/module-b0`.

## What is pinned and what can change

The Fedora image is `Fedora-Cloud-Base-Generic-44-1.7.aarch64.qcow2`, with SHA-256 `55c60a3b80d3616a08705afd0459e75fe9f03c54aba7a46e4002a41a72fa0d5b`. The template contains its full release URL. Ubuntu's template separately pins dated images for both supported architectures.

The course version is `v2.0.0-beta.1`. Provisioning downloads its archive and `SHA256SUMS`, checks the selected artifact, and validates the installed course before writing readiness. Checksums obtained from the same release detect mismatches, not compromise of the release publisher.

Package repositories still deliver current package revisions; an image digest does not freeze later package installation. Deployment evidence records exact installed versions. Fedora consumes `deploy/fedora-packages.txt`; Ubuntu and GitHub Actions consume `deploy/ubuntu-packages.txt`. They are distinct distro package names, not interchangeable lists. CI's Ubuntu jobs do not substitute for a booted Fedora validation run.

Both templates use Lima plain mode without host mounts, guest agent, dynamic port forwarding, built-in container runtime, Rosetta, or SSH-agent forwarding. Shell access, readiness probes, and file copy use SSH. Plain-mode copy and a deliberately failing readiness probe are part of appliance acceptance, not merely assumptions.

## Restart, export, and reset

Exit the guest shell with `exit`. These commands run on the **Mac host**:

```bash
limactl stop north-echo-beta
limactl start north-echo-beta
limactl shell north-echo-beta
```

A readiness marker makes normal restarts idempotent: they do not reinstall over your source or re-extract over student work. Restarting an old release does not upgrade it. To review another version, use another instance or separately validated directory.

Export the synthetic first-install evidence from the **host**:

```bash
limactl copy north-echo-beta:~/north-echo-deployment-evidence.tgz .
```

This is not a backup of your solutions. To save work, run inside the **guest course root**:

```bash
tar -czf ~/north-echo-student-work.tgz .student .state
```

Then copy it from the **host**:

```bash
limactl copy north-echo-beta:~/north-echo-student-work.tgz .
```

Keep the work archive private: it contains solutions and notes. Verify it reached the host before deleting anything.

Deleting/recreating is the factory reset, and destroys **all unexported work in that exact VM**. Only after export and only if you want a clean instance:

```bash
limactl delete -f north-echo-beta
limactl start --name north-echo-beta deploy/north-echo-fedora.yaml
```

No deletion is needed for an ordinary restart or a single lesson reset.

## Ubuntu compatibility path

Use a different new instance name on the **host**:

```bash
limactl start --name north-echo-beta-ubuntu deploy/north-echo.yaml
limactl shell north-echo-beta-ubuntu
```

Then follow the same guest course-root and B0 steps. Do not use the Fedora package list with apt. The Ubuntu installer applies the narrow course AppArmor profile only if the ordinary user-namespace check requires it; it does not disable AppArmor globally.

## Manual provisioning inside a disposable Linux VM

First create an ordinary account and log in as that account. These are **guest** commands. For Fedora:

```bash
sudo dnf install -y git ca-certificates
git clone --branch v2.0.0-beta.1 --depth 1 https://github.com/north-echo/north-echo-agent-security-lab.git north-echo
cd north-echo
xargs sudo dnf install -y < deploy/fedora-packages.txt
test "$(getenforce)" = Enforcing
```

For Ubuntu, use this alternative, not both blocks:

```bash
sudo apt-get update
sudo apt-get install -y git ca-certificates
git clone --branch v2.0.0-beta.1 --depth 1 https://github.com/north-echo/north-echo-agent-security-lab.git north-echo
cd north-echo
xargs sudo apt-get install -y < deploy/ubuntu-packages.txt
if ! unshare --user --map-root-user true; then
  sudo install -m 0644 validation/apparmor-north-echo-unshare /etc/apparmor.d/north-echo-unshare
  sudo apparmor_parser -r /etc/apparmor.d/north-echo-unshare
fi
```

Then on either guest, enable the **actual ordinary user's** manager and validate:

```bash
test "$(id -u)" -ne 0
sudo loginctl enable-linger "$(id -un)"
./scripts/linux-preflight
./scripts/attest-course
python3 scripts/run_tests.py --require-no-skips
```

Do not run these from a root shell: `id -un` must identify the learner, not root. If the user manager is unavailable, log out and back into the guest as that account, then retry. Do not run lessons with sudo to bypass a failure.

## Troubleshooting without weakening the boundary

A failed readiness probe returns failure but does not necessarily power the guest off. Stop it explicitly from the host if required. Inspect the guest's `/var/log/cloud-init-output.log` and deployment evidence. Do not treat a booted login prompt as successful course validation.

If installation left `~/north-echo` but no readiness marker, the installer refuses to overwrite it. Export anything needed and recreate that disposable instance. Do not hand-create a readiness marker to suppress failures.

For a failing preflight, keep the exact failing check and environment versions. Static compilation, actual Landlock/seccomp enforcement, and effective user-manager limits are required—not just installed command names. Keep SELinux enforcing and AppArmor enabled. Never modify your Mac, employer host, LAN firewall, or shared server to force a lesson to pass.

The [source/version companion](SOURCE_TRUTH.md) explains baseline differences. The [Linux validation matrix](LINUX_VALIDATION.md) is the maintainer acceptance procedure, not extra required beginner homework. Lima's [official documentation](https://lima-vm.io/docs/) is optional setup reference.
