# 10.02 - Seal filesystem and syscall policy before exec

## Goal

Observe an unrestricted native probe, then place the same static executable behind one guard that applies Landlock before a native-architecture, default-deny seccomp filter.

## Exercise 1 - Read and compile the complete programs

```bash
sed -n '1,360p' runtime_guard.c
sed -n '1,240p' guard_probe.c
gcc -O2 -Wall -Wextra -static runtime_guard.c -o runtime_guard -lseccomp
gcc -O2 -Wall -Wextra -static guard_probe.c -o guard_probe
```

### Line by line

- Both `sed` commands display the complete local sources before execution.
- `-O2` makes an ordinary optimized binary; `-Wall -Wextra` keep diagnostics visible; `-static` removes post-policy dynamic-loader dependencies.
- Only the guard links libseccomp because the probe merely observes the installed filter.

### `runtime_guard.c`, block by block

- The syscall wrappers query the running Landlock ABI. `supported_rights` handles filesystem rights explicitly named by this source and available in its build headers, gated by their runtime ABI. Like Module 05, it includes `REFER`, `TRUNCATE`, and conditionally `IOCTL_DEV` and `RESOLVE_UNIX`. Newer unnamed rights are not automatically denied.
- `install_landlock` grants the workload root execute/read access and, with ABI 9 headers and kernel support, pathname Unix-socket resolution. It grants `/proc` and `/sys/fs/cgroup` read access for observations, but no Unix-socket resolution there. These are explicit observability exceptions: this is not a private PID or mount view. Unmentioned paths receive no handled access. Device IOCTL is handled but never granted; seccomp also omits `ioctl`.
- The ABI message identifies runtime support, not build-header completeness. On the Ubuntu baseline, newer rights that the headers cannot name remain a reviewed source property rather than a demonstrated kernel guarantee.
- `PR_SET_NO_NEW_PRIVS` precedes `landlock_restrict_self`; a regular user cannot otherwise enforce the ruleset on itself.
- `install_seccomp` starts from `EPERM`, adds a small static-program syscall surface, and allows `socket` only when argument zero is `AF_UNIX`. `AF_INET` and alternate socket domains therefore remain denied by the default.
- The guard loads the filter only after Landlock setup is complete and calls `execv` with the original argv boundaries.

### `guard_probe.c`, block by block

- `readable` performs a real `open` and `read`; it does not infer access from path text or mode bits.
- `status_number` reads the probe's own `NoNewPrivs` and `Seccomp` fields from `/proc/self/status`.
- `main` reads one allowed and one protected file, attempts an IPv4 socket, and prints observed return values and kernel state.

Static linking keeps the execution policy small: the post-Landlock `exec` does not need dynamic-loader reads from host library directories.

## Exercise 2 - Observe the incomplete launch

```bash
DEMO=$(mktemp -d /tmp/north-echo-10.02.XXXXXX)
mkdir "$DEMO/allowed"
cp guard_probe "$DEMO/allowed/guard_probe"
printf 'allowed\n' > "$DEMO/allowed/input.txt"
printf 'synthetic-protected\n' > "$DEMO/protected.txt"
"$DEMO/allowed/guard_probe" "$DEMO/allowed/input.txt" "$DEMO/protected.txt"
```

Expected patterns are `allowed=1 protected=1`, a nonnegative `inet_fd`, and the host process's seccomp/no-new-privileges values. The intentional mistake is launching the probe merely because its binary is trusted. Nothing prevents it from opening the protected file or creating an IP socket.

## Exercise 3 - Repair with ordered kernel policy

```bash
./runtime_guard "$DEMO/allowed" "$DEMO/allowed/guard_probe" \
  "$DEMO/allowed/input.txt" "$DEMO/protected.txt"
```

Expected patterns are:

```text
allowed=1 protected=0 protected_errno=Permission denied inet_fd=-1 inet_errno=Operation not permitted nnp=1 seccomp=2
```

- The allowed read proves the policy did not simply break all file access.
- `Permission denied` is an effective Landlock observation against a file whose Unix mode still permits the user.
- `AF_INET` returns `EPERM`, while Lesson 10.03 will prove the explicitly allowed `AF_UNIX` broker path still works.
- `NoNewPrivs: 1` and `Seccomp: 2` are kernel-reported state after `exec`, not claims made by the launcher.

Clean only the exact lesson objects:

```bash
rm "$DEMO/allowed/guard_probe" "$DEMO/allowed/input.txt" "$DEMO/protected.txt"
rmdir "$DEMO/allowed" "$DEMO"
rm runtime_guard guard_probe
```

## Checkpoint and troubleshooting

```bash
test ! -e "$DEMO" || { echo "lesson temporary directory remains" >&2; false; }
```

- If static linking fails, install the packages named by `./scripts/linux-preflight`; do not weaken the Landlock policy to expose host libraries.
- If Landlock reports unsupported, use the disposable VM kernel required by Module 05.
- If `execv` returns `EPERM`, confirm the static workload executable is beneath the allowed root and Landlock was installed before seccomp.
- Checkpoint: explain why seccomp mode 2 does not prove pathname confinement, and why a protected-file denial does not prove IP denial.
