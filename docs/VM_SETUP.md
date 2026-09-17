# Disposable Linux VM setup

Recommended: Ubuntu 24.04 or Debian 12, 2 vCPU, 4 GiB RAM, 20 GiB disk, NAT networking, and a snapshot taken immediately after package installation.

Install prerequisites:

```bash
sudo apt-get update
sudo apt-get install -y build-essential python3 strace util-linux libcap2-bin procps
```

For the Linux-backed development hand-off that will build Modules 04-12, install the additional local-only tooling now so later tranche work can probe Landlock, seccomp, cgroups, and network namespaces without changing machines:

```bash
sudo apt-get install -y linux-libc-dev libseccomp-dev pkg-config iproute2 nftables jq
```

These packages provide headers and administration tools; installing them does not authorize a lesson to change host-global networking or cgroups. Later lessons must create isolated, registered resources and prove ownership before cleanup.

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

The platform itself needs Python 3.9+ and standard Unix tools. Module 01 needs a C compiler and `strace`; Module 02 needs `unshare`, procfs, and enabled user namespaces; Module 03 needs `capsh` and `setpriv`; Module 05 needs Linux `openat2` and Landlock UAPI headers plus kernel support; Module 06 needs `pkg-config`, libseccomp development files, seccomp filter mode, and a static C toolchain. Later modules add explicit prerequisites only as they become playable.

Before opening the continuation task, run:

```bash
./scripts/linux-preflight
```

Then follow [LINUX_VALIDATION.md](LINUX_VALIDATION.md). A missing future-module capability is information to design around or document; it is not permission to disable a host security control.
