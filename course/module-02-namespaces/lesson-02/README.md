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

Expected pattern: inside changes to `north-echo-lab`; host before and host after are identical. The child needs a user namespace so its mapped root has the capability needed to set the UTS hostname in the new UTS namespace.

## Exercise 2 - Make the intentional mistake

Try only:

```bash
unshare --uts hostname broken-attempt
```

As an ordinary user, expected: `Operation not permitted`. Creating a UTS namespace does not by itself grant the authority needed by this invocation. Compose namespaces deliberately.

## Exercise 3 - Compare effective state

In one terminal:

```bash
unshare --user --map-root-user --uts sh -c 'hostname north-echo-hold; echo $$; sleep 60'
```

Using the printed host-visible PID in another terminal:

```bash
readlink /proc/PRINTED_PID/ns/uts
readlink /proc/self/ns/uts
```

Expected: different handles. End the sleeping process with `Ctrl-C`. Verification is about the resulting namespace membership, not the presence of `unshare` in a script.
