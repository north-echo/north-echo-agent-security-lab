# 02.01 - Read namespace identity

Goal: compare namespace membership using kernel-provided handles instead of assuming a container-like command worked.

## Exercise 1 - Capture the baseline

```bash
printf '%-8s %s\n' TYPE HANDLE
for ns in user uts pid mnt net ipc cgroup; do
  printf '%-8s %s\n' "$ns" "$(readlink /proc/self/ns/$ns)"
done
```

### Line by line

- `printf '%-8s %s\n' TYPE HANDLE` prints column headings; `%-8s` left-aligns a string in an eight-character field.
- `for ns in ...; do` begins a shell loop and assigns each namespace name to `ns` in turn.
- `$(readlink /proc/self/ns/$ns)` asks procfs for the current process's handle for that namespace and substitutes the result.
- `"$ns"` is quoted so the expansion remains one argument. The surrounding command substitution is quoted for the same reason.
- `done` closes the loop.

Expected pattern: each handle looks like `type:[inode]`. Equality means two processes refer to the same namespace object for that type.

## Exercise 2 - Create a user namespace

```bash
unshare --user --map-root-user sh -c '
  echo "inside uid=$(id -u)";
  readlink /proc/self/ns/user;
  cat /proc/self/uid_map
'
```

### Line by line

- `unshare` creates new namespaces for the command that follows.
- `--user` requests a new user namespace; `--map-root-user` maps your current host identity to UID/GID 0 inside it.
- `sh -c '...'` starts a shell and supplies the quoted multi-line string as its program.
- `id -u` prints the effective numeric UID seen inside the namespace.
- `readlink .../user` prints the new user-namespace identity.
- `cat /proc/self/uid_map` shows how inside UIDs translate to IDs in the parent namespace.

Expected pattern: `inside uid=0`, a user namespace handle different from your baseline, and a map tying namespace UID 0 to your ordinary host UID. Namespace root is not host root.

If this returns `Operation not permitted`, stop. Enable unprivileged user namespaces in the disposable VM; do not run the course on a work host to work around it.

## Exercise 3 - Catch an intentional reasoning mistake

Mistaken claim: “UID 0 means the process is privileged everywhere.” Test it:

```bash
unshare --user --map-root-user sh -c 'id; touch /root/north-echo-test'
```

### Line by line

- The `unshare` flags create the same mapped user namespace as the previous block.
- Inside the quoted shell program, `;` sequences commands regardless of whether the previous command succeeds.
- `id` reports the namespace-visible identity.
- `touch /root/north-echo-test` asks the kernel to create a file through the host-mounted `/root` path; the expected denial demonstrates the boundary between namespace identity and parent-namespace authority.

Expected: `id` reports UID 0 inside, but writing the host's `/root` fails. The user namespace changes credential interpretation; it does not grant authority in the parent namespace.

Checkpoint: always record both the namespace handle and the ID mapping when explaining identity.
