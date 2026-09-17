# 02.02 - Change UTS state without changing the host

Goal: isolate hostname state and prove the parent is unchanged.

## Exercise 1 - Baseline and isolated change

```bash
HOST_BEFORE=$(hostname)
echo "host before=$HOST_BEFORE"
unshare --user --map-root-user --uts sh -c '
  echo "inside before=$(hostname)";
  hostname north-echo-lab;
  echo "inside after=$(hostname)";
  readlink /proc/self/ns/uts
'
echo "host after=$(hostname)"
```

### Line by line

- `HOST_BEFORE=$(hostname)` captures the host-visible hostname in a shell variable; it is not exported to children unless requested.
- `echo "host before=$HOST_BEFORE"` records the baseline using quoted variable expansion.
- `--user --map-root-user` creates capability inside a new user namespace, while `--uts` creates an isolated hostname/domain-name view.
- The first inner `echo` reads the hostname before changing it.
- `hostname north-echo-lab` requests the UTS state change inside the new namespace.
- The second inner `echo` observes the change, and `readlink` records the effective UTS namespace handle.
- The final host-side `echo` runs after `unshare` exits and proves the parent namespace value did not change.

Expected pattern: inside changes to `north-echo-lab`; host before and host after are identical. The child needs a user namespace so its mapped root has the capability needed to set the UTS hostname in the new UTS namespace.

## Exercise 2 - Make the intentional mistake

Try only:

```bash
unshare --uts hostname broken-attempt
```

### Line by line

- `--uts` requests only a UTS namespace.
- `hostname broken-attempt` is the command `unshare` tries to execute inside it.
- No mapped user namespace is created, so an ordinary user normally lacks the capability required to complete this setup.

As an ordinary user, expected: `Operation not permitted`. Creating a UTS namespace does not by itself grant the authority needed by this invocation. Compose namespaces deliberately.

## Exercise 3 - Compare effective state

In one terminal:

```bash
unshare --user --map-root-user --uts sh -c 'hostname north-echo-hold; echo $$; sleep 60'
```

### Line by line

- The namespace flags establish mapped user and isolated UTS state.
- `hostname north-echo-hold` gives the temporary namespace a recognizable value.
- `echo $$` prints the shell's host-visible PID so another terminal can inspect `/proc/PID`.
- `sleep 60` keeps the process and its namespaces alive for inspection; `Ctrl-C` ends it early.

Using the printed host-visible PID in another terminal:

```bash
readlink /proc/PRINTED_PID/ns/uts
readlink /proc/self/ns/uts
```

### Line by line

- Replace `PRINTED_PID` with the decimal PID from the first terminal; do not type the word literally.
- The first `readlink` observes the held process's UTS namespace.
- `/proc/self` always refers to the inspecting process, so the second line records your current shell's UTS namespace for comparison.

Expected: different handles. End the sleeping process with `Ctrl-C`. Verification is about the resulting namespace membership, not the presence of `unshare` in a script.
