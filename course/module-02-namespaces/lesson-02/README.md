# 02.02 - Change UTS state without changing the host

## Goals

- Isolate hostname state in a UTS namespace.
- Understand why namespace creation and authority to modify its state are separate concerns.
- Compare host and child state before and after the change.
- Inspect a live process from another terminal.

## Exercise 1 - Baseline, change, and proof

Complete 02.01 first. A UTS namespace stores a hostname and NIS domain name. It does not create a new network stack, DNS service, or machine. The hostname starts as a copy; changing the copy must leave the parent VM's hostname unchanged.

From the course root, prepare this shell-only lesson:

```bash
./lab-start 02.02
cd .student/02.02
pwd
ls -l
```

The first command creates the student workspace; the next three enter and inspect it. There is no source file to compile. Predict the two `host` lines before running the next block: they should be identical. Here "host" means the parent VM environment, not the Mac.

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

## What each line does

- The first command substitution captures the parent-visible hostname.
- The variable is local to this shell unless exported.
- `--user --map-root-user` creates namespace-local capability; `--uts` creates an isolated UTS view.
- Single quotes defer inner `hostname` substitutions until the child shell runs.
- The first inner line observes the initial copied hostname.
- `hostname north-echo-lab` changes only the new UTS namespace.
- The second inner observation proves the new value.
- `readlink` records the namespace identity associated with that state.
- The final line runs back in the parent after `unshare` exits and proves the host value is unchanged.

Expected relationship:

```text
host before=<vm hostname>
inside before=<vm hostname>
inside after=north-echo-lab
uts:[different handle]
host after=<same vm hostname>
```

The mapped user namespace gives the process the relevant capability inside the newly owned UTS namespace. It does not create host authority.

## Exercise 2 - Make the incomplete attempt

```bash
unshare --uts hostname broken-attempt
```

- `--uts` requests only a UTS namespace.
- `hostname broken-attempt` is the command to run inside it.
- An ordinary user generally lacks the capability needed for this setup without the mapped user namespace.
- Expected: `Operation not permitted` and no host change.

The failure is useful. Creating a namespace type does not automatically supply every credential needed to configure it.

## Exercise 3 - Inspect a live namespace

In terminal one:

```bash
unshare --user --map-root-user --uts sh -c 'hostname north-echo-hold; echo $$; sleep 60'
```

- The flags create the temporary user and UTS namespaces.
- `hostname` assigns a recognizable value.
- `echo $$` prints the shell's PID as seen from the parent namespace running the terminal.
- `sleep 60` keeps the process and namespace alive. `Ctrl-C` ends it early.

Open a second terminal and enter the **same VM**, using the same `limactl shell INSTANCE_NAME` command you used for terminal one. Do not run the following inspection on the Mac or in a different VM. For example, if the first command printed `12345`, replace `PRINTED_PID` below with `12345`; do not type the placeholder literally. In terminal two:

```bash
readlink /proc/PRINTED_PID/ns/uts
readlink /proc/self/ns/uts
```

- The first line observes the held process's UTS namespace.
- `/proc/self` in the second terminal refers to the inspecting process.
- Different handles prove different membership even if both hostnames happened to contain the same text.

Verification should inspect effective state, not merely search a script for the word `unshare`.

## Exercise 4 - Preserve an argument vector through a shell

The independent lab will accept a command and its arguments. A shell wrapper must preserve their boundaries, including arguments containing spaces. Practice that separately from namespace setup:

```bash
NE_PRACTICE_LABEL=example sh -c '
  printf "label=%s script-name=%s\n" "$NE_PRACTICE_LABEL" "$0"
  exec "$@"
' practice-wrapper /usr/bin/printf '<%s>\n' 'two words' final
```

- The leading assignment puts a synthetic label in this child's environment. Reading a supplied value differs from hard-coding a particular fixture value.
- `sh -c` consumes one argument as its program. The next, `practice-wrapper`, becomes `$0`, the shell's script name. It is **not** part of `$@`.
- The remaining arguments become `$1`, `$2`, and so forth. `"$@"` expands them as separate arguments, preserving the original boundaries.
- `exec` replaces the shell with that argument vector. It does not concatenate and reinterpret a command string.
- `/usr/bin/printf` receives its format followed by two data arguments. Expect `<two words>` on one line and `<final>` on another.

Deliberately change `exec "$@"` to `exec $@` in the command you type and repeat. The unquoted expansion splits `two words` into separate arguments: the output becomes three data lines. Restore the quotes and verify two lines again. This error can be invisible when every test argument is a single word.

For a script file, the corresponding concepts are `#!/bin/sh` on the first line, `$1` for its first supplied argument, and `exec "$@"` to replace it. The starter in the independent lab shows that minimal script. Combine this practiced argument handling with the namespace controls yourself; do not turn the supplied command into text for another shell to parse.

## Troubleshooting and checkpoint

- If the first terminal exits before inspection, rerun with a longer harmless sleep.
- If `/proc/PRINTED_PID` is absent, confirm you used the host-visible PID and that the process is still alive.
- If the handles match, inspect the exact flags and quoting rather than changing the expected result.
- You should be able to state why the parent hostname remains unchanged.

Finish with `hostname` in terminal one after the child exits and compare it with `echo "$HOST_BEFORE"`. That comparison plus the different namespace handles is the checkpoint: a successful command alone does not prove isolation. The deliberately incomplete attempt in Exercise 2 is repaired by the mapped user namespace in Exercise 1, never by running the lesson as global root.

After the child exits, its private hostname disappears with the namespace. If you reset the workspace, run `cd ../..` followed by `./lab-reset 02.02` in terminal one; do not try to "restore" the parent hostname with a privileged command.

## Source truth

See [uts_namespaces(7)](https://man7.org/linux/man-pages/man7/uts_namespaces.7.html) for isolated hostname state and [user_namespaces(7)](https://man7.org/linux/man-pages/man7/user_namespaces.7.html) for the ownership-based capability check.
