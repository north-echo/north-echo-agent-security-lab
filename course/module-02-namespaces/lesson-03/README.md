# 02.03 - PID namespaces and the procfs mistake

## Goals

- Start a shell as PID 1 inside a new PID namespace.
- Observe why an inherited procfs can show the wrong process view.
- Compose PID and mount namespaces with a matching procfs.
- Recognize the responsibilities assigned to namespace PID 1.

## Exercise 1 - Create the incomplete setup

Complete 02.01 and 02.02 first. A PID is a process identifier **within a PID namespace**. The same process can have one number inside a child namespace and another in its parent. PID 1 is the first process in the child namespace and has special lifecycle responsibilities. A mount namespace separately controls which filesystem mounts are visible. We need both concepts because `ps` obtains its information from a mounted filesystem, `/proc`.

From the course root:

```bash
./lab-start 02.03
cd .student/02.03
pwd
ls -l
```

These commands prepare, enter, and inspect this shell-only workspace. There is no source file to open. Predict whether changing process numbering alone will automatically replace an existing `/proc` mount. Exercise 1 deliberately leaves that second control out.

```bash
unshare --user --map-root-user --pid --fork sh -c '
  echo "shell says pid=$$";
  ps -o pid,ppid,comm | head
'
```

## What each line does

- The mapped user namespace provides safe namespace-local authority.
- `--pid` creates a PID namespace for children, not retroactively for the calling `unshare` process.
- `--fork` creates the child that can enter the new PID namespace.
- The quoted shell runs as the namespace's first process and expands its own `$$`.
- `ps` obtains process data through the currently mounted `/proc`.
- `head` limits display but cannot correct the underlying view.

Expected surprise: the shell reports PID 1 while `ps` may show many host processes or numbers that do not agree. The PID namespace changed, but the inherited procfs mount still represents the parent PID namespace.

## Exercise 2 - Mount a matching procfs

```bash
unshare --user --map-root-user --pid --fork --mount --mount-proc sh -c '
  echo "shell says pid=$$";
  ps -o pid,ppid,comm;
  echo "pid namespace=$(readlink /proc/self/ns/pid)";
  echo "mount namespace=$(readlink /proc/self/ns/mnt)"
'
```

## What each line does

- `--mount` isolates mount-table changes from the parent.
- `--mount-proc` mounts a fresh procfs associated with the new PID namespace.
- `--pid --fork` creates and enters the PID namespace in the required child.
- The shell sees itself as PID 1.
- `ps` now reads the fresh procfs, so its process list should agree with the namespace-local IDs.
- The two `readlink` calls record both namespace identities.

Expected: a small process list containing the shell and observation tools, plus new PID and mount handles. Process counts can vary because `ps`, shells, and pipelines briefly create processes.

## Exercise 3 - Wait for a known child

```bash
unshare --user --map-root-user --pid --fork --mount --mount-proc sh -c '
  (exit 7) &
  child=$!
  wait "$child"
  result=$?
  echo "waited for child=$child status=$result"
  ps -o pid,ppid,stat,comm
'
```

## What each line does

- Parentheses create a subshell; `exit 7` gives it a recognizable nonzero status.
- `&` runs that subshell asynchronously.
- `$!` gives the last background child's PID; save it immediately rather than guessing it from the process list.
- `wait "$child"` collects the status for that child. The shell may already have reaped it internally; `wait` still retrieves the saved result.
- Save `$?` before another command replaces it. The expected status is 7, not a namespace failure.
- The final `ps` shows the remaining processes. Do not expect the exited child to remain in the list.

This demonstrates waiting for a known direct child. It does **not** test orphan adoption, zombie accumulation, or a general-purpose init implementation. A shell may automatically reap children, so a snapshot with no `Z` rows is not proof that an arbitrary application is a suitable init.

Namespace PID 1 has special signal behavior and becomes the adopter for orphaned descendants. A production runtime normally supplies a small init/reaper instead of casually making an arbitrary workload PID 1.

## Why namespace composition matters

A PID namespace without a matching procfs produces contradictory observations. A UTS namespace without suitable namespace-local authority may not be configurable. A mount namespace does not automatically create a private filesystem tree. Namespaces isolate selected views; they are components, not a complete sandbox policy.

## Troubleshooting and checkpoint

- If `--mount-proc` fails, confirm the mapped user namespace was created and the util-linux `unshare` version supports it.
- If `ps` shows the host, compare the mount namespace handle and inspect the active `/proc` mount.
- Do not grade by exact process count; grade by namespace relationships and the procfs view.
- You should be able to explain why `$$` and `ps` disagreed in the incomplete setup.

For your checkpoint, describe the missing control in Exercise 1, run the repaired Exercise 2, and explain why a changed PID handle alone would be insufficient evidence. Never change the VM's real `/proc` mount to repair this lesson. The private mounts vanish with their namespace after the command ends.

To discard the workspace, return with `cd ../..` and run `./lab-reset 02.03`. This does not erase other lessons.

## Source truth

See [pid_namespaces(7)](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html) for PID 1, visibility, and procfs relationships; [unshare(1)](https://man7.org/linux/man-pages/man1/unshare.1.html) for `--fork` and `--mount-proc`; and the VM's `help wait` for the shell builtin.
