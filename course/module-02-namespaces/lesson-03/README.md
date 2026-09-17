# 02.03 - PID namespaces and the /proc mistake

Goal: create a process as PID 1 inside a namespace, observe stale `/proc`, then mount a matching procfs.

## Exercise 1 - The incomplete setup

```bash
unshare --user --map-root-user --pid --fork sh -c '
  echo "shell says pid=$$";
  ps -o pid,ppid,comm | head
'
```

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

Expected pattern: the shell is PID 1 and `ps` shows only the small namespace-local process set. `--mount-proc` creates a mount namespace and mounts procfs for the new PID namespace.

## Exercise 3 - Observe PID 1 responsibility

```bash
unshare --user --map-root-user --pid --fork --mount --mount-proc sh -c '
  (exit 0) &
  sleep 0.2
  ps -o pid,ppid,stat,comm
'
```

Expected: your namespace init is responsible for orphan adoption and reaping. A production runtime normally provides an init/reaper rather than casually making the workload PID 1.

Security conclusion: namespaces isolate views one resource class at a time. Correct composition and effective-state verification matter more than the word “namespace.”
