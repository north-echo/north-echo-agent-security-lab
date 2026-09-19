# Disposable Linux VM setup

Validated baseline: Ubuntu 24.04 on x86-64 or arm64, 4 vCPU, 6 GiB RAM, 30 GiB disk, NAT networking. Debian 12 is a candidate baseline, not yet acceptance-tested. For a manually created VM, take a snapshot after successful provisioning.

## Pinned Lima appliance on macOS

Lima 2.2 or newer is the shortest supported path on macOS. The template uses Lima plain mode: no host filesystem mount, dynamic port forwarding, built-in container runtime, guest agent, Rosetta, or SSH-agent forwarding. It pins dated Ubuntu 24.04 amd64 and arm64 cloud images by SHA-256 and installs the course from a checksum-verified GitHub release archive.

```bash
git clone https://github.com/north-echo/north-echo-agent-security-lab.git
cd north-echo-agent-security-lab
limactl start --name north-echo deploy/north-echo.yaml
limactl shell north-echo
cd ~/north-echo
./lab-start 01.01
cd .student/01.01
less README.md
```

Provisioning is idempotent. A readiness marker prevents a normal restart from reinstalling packages or extracting over student work. If provisioning failed after creating `~/north-echo`, the next start refuses to overwrite it; delete and recreate the disposable instance:

```bash
limactl delete -f north-echo
limactl start --name north-echo deploy/north-echo.yaml
```

The successful first boot writes a synthetic deployment-evidence archive outside the repository. Export it without enabling a host mount:

```bash
limactl copy north-echo:~/north-echo-deployment-evidence.tgz .
```

The Ubuntu package manifest is [deploy/ubuntu-packages.txt](../deploy/ubuntu-packages.txt). GitHub Actions and the Lima appliance both consume that exact file.

Image bytes and the course archive are pinned. Ubuntu package repositories can
still deliver newer packages at installation time; the appliance records exact
installed revisions in `packages.tsv` inside deployment evidence. The template's
`CourseVersion` selects a published archive and intentionally does not track
unreleased working-tree changes. Student work is preserved on ordinary restarts;
testing a new course revision requires a new instance or a separate validation copy.

## Manual VM setup

Install prerequisites:

```bash
sudo apt-get update
sudo apt-get install -y git ca-certificates
git clone https://github.com/north-echo/north-echo-agent-security-lab.git
cd north-echo-agent-security-lab
xargs sudo apt-get install -y < deploy/ubuntu-packages.txt
```

Enable the ordinary user's manager, and apply the scoped Ubuntu AppArmor profile only if the user-namespace check fails. These are provisioning steps inside the disposable VM:

```bash
sudo loginctl enable-linger "$(id -un)"
if ! unshare --user --map-root-user true; then
  sudo install -m 0644 validation/apparmor-north-echo-unshare /etc/apparmor.d/north-echo-unshare
  sudo apparmor_parser -r /etc/apparmor.d/north-echo-unshare
fi
./scripts/linux-preflight
```

The manifest supplies headers, static development libraries, and runtime tools for all twelve modules. Preflight must establish effective kernel policy and delegated limits before the VM is considered ready. If the user manager is unavailable, log out and back in as the ordinary user, then retry; do not run the labs with sudo.

Use an ordinary account:

```bash
id -u
test "$(id -u)" -ne 0
```

Expected: the second command exits 0.

Check required kernel interfaces:

```bash
test -r /proc/self/status
test -e /proc/self/ns/user
unshare --user --map-root-user true
```

All three should exit 0. On distributions that intentionally disable unprivileged user namespaces, change that setting only in this disposable VM according to the distribution's documentation. Do not weaken a work machine or shared server.

Use the baseline's Python 3.12 and standard Unix tools. Module 01 needs a C compiler and `strace`; Module 02 needs `unshare`, procfs, and enabled user namespaces; Module 03 needs `capsh` and `setpriv`; Module 05 needs working `openat2` and Landlock; Module 06 needs libseccomp and a static C toolchain; Modules 07 and 10 need effective delegated cgroup v2 CPU, memory, swap, and task limits. Modules 08-09 need local Unix sockets and unprivileged network namespaces.

Before opening a lesson, run:

```bash
./scripts/linux-preflight
```

Then run `./scripts/attest-course` and `./lab-start 01.01`. The [Linux validation matrix](LINUX_VALIDATION.md) is the maintainer acceptance procedure.

## Export student work before deleting a VM

Inside the guest, from `~/north-echo`, create an archive containing only course work:

```bash
tar -czf ~/north-echo-student-work.tgz .student .state
```

From the host:

```bash
limactl copy north-echo:~/north-echo-student-work.tgz .
```

Keep this private: it contains your solutions. This is separate from the synthetic deployment-evidence archive. VM deletion removes all unexported student work. A normal `limactl stop north-echo` followed by `limactl start north-echo` preserves it.
