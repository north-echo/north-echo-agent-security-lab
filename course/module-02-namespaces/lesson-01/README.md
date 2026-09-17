# 02.01 - Read namespace identity

Goal: compare namespace membership using kernel-provided handles instead of assuming a container-like command worked.

## Exercise 1 - Capture the baseline

```bash
printf '%-8s %s\n' TYPE HANDLE
for ns in user uts pid mnt net ipc cgroup; do
  printf '%-8s %s\n' "$ns" "$(readlink /proc/self/ns/$ns)"
done
```

Expected pattern: each handle looks like `type:[inode]`. Equality means two processes refer to the same namespace object for that type.

## Exercise 2 - Create a user namespace

```bash
unshare --user --map-root-user sh -c '
  echo "inside uid=$(id -u)";
  readlink /proc/self/ns/user;
  cat /proc/self/uid_map
'
```

Expected pattern: `inside uid=0`, a user namespace handle different from your baseline, and a map tying namespace UID 0 to your ordinary host UID. Namespace root is not host root.

If this returns `Operation not permitted`, stop. Enable unprivileged user namespaces in the disposable VM; do not run the course on a work host to work around it.

## Exercise 3 - Catch an intentional reasoning mistake

Mistaken claim: “UID 0 means the process is privileged everywhere.” Test it:

```bash
unshare --user --map-root-user sh -c 'id; touch /root/north-echo-test'
```

Expected: `id` reports UID 0 inside, but writing the host's `/root` fails. The user namespace changes credential interpretation; it does not grant authority in the parent namespace.

Checkpoint: always record both the namespace handle and the ID mapping when explaining identity.
