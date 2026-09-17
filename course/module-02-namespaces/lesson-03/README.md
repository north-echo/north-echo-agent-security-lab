# 02.03 - PID namespaces and the /proc mistake

Goal: create a process as PID 1 inside a namespace, observe stale `/proc`, then mount a matching procfs.

## Exercise 1 - The incomplete setup

```bash
unshare --user --map-root-user --pid --fork sh -c '
  echo "shell says pid=$$";
  ps -o pid,ppid,comm | head
'
```

### Line by line

- `--pid` creates a PID namespace for children; `--fork` is required so `unshare` can place a newly forked child into it.
- `sh -c` runs the quoted observations as that child.
- `$$` expands inside the child shell and therefore reports the namespace-local PID.
- `ps -o ...` reads process information through the existing `/proc` mount.
- `| head` limits display, but the stale mount can still expose the parent namespace's process view.

Expected surprise: the shell says PID 1, but `ps` may display the host's process view. This is the intentional mistake. PID interpretation changed; the existing `/proc` mount did not.

## Exercise 2 - Add a mount namespace and matching procfs

```bash
unshare --user --map-root-user --pid --fork --mount --mount-proc sh -c '
  echo "shell says pid=$$";
  ps -o pid,ppid,comm;
  echo "pid namespace=$(readlink /proc/self/ns/pid)";
  echo "mount namespace=$(readlink /proc/self/ns/mnt)"
'
```

### Line by line

- `--mount` creates a new mount namespace so mount changes stay out of the parent.
- `--mount-proc` mounts a fresh procfs associated with the new PID namespace.
- `--pid --fork` creates the child PID namespace and starts the shell as its first process.
- `ps -o pid,ppid,comm` now reads the newly mounted procfs, so its view should agree with the namespace-local `$$` value.
- The two `readlink` commands record the effective PID and mount namespace identities.

Expected pattern: the shell is PID 1 and `ps` shows only the small namespace-local process set. `--mount-proc` creates a mount namespace and mounts procfs for the new PID namespace.

## Exercise 3 - Observe PID 1 responsibility

```bash
unshare --user --map-root-user --pid --fork --mount --mount-proc sh -c '
  (exit 0) &
  sleep 0.2
  ps -o pid,ppid,stat,comm
'
```

### Line by line

- `(exit 0) &` starts a background subshell that exits immediately; parentheses create the subshell and `&` runs it asynchronously.
- `sleep 0.2` gives the kernel and shell time to process the child's exit.
- `ps ... stat ...` includes the process-state column, which is where a zombie would appear as `Z` if PID 1 failed to reap it.

Expected: your namespace init is responsible for orphan adoption and reaping. A production runtime normally provides an init/reaper rather than casually making the workload PID 1.

Security conclusion: namespaces isolate views one resource class at a time. Correct composition and effective-state verification matter more than the word “namespace.”
