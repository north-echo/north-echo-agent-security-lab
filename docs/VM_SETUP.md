# Disposable Linux VM setup

Recommended: Ubuntu 24.04 or Debian 12, 2 vCPU, 4 GiB RAM, 20 GiB disk, NAT networking, and a snapshot taken immediately after package installation.

Install prerequisites:

```bash
sudo apt-get update
sudo apt-get install -y build-essential python3 strace util-linux libcap2-bin procps
```

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

The platform itself needs Python 3.9+ and standard Unix tools. Module 01 needs a C compiler and `strace`; Module 02 needs `unshare`, procfs, and enabled user namespaces; Module 03 needs `capsh` and `setpriv`. Later modules will add explicit prerequisites as they become playable.
