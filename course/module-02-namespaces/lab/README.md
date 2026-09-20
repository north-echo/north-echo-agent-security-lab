# Module 02 independent lab - Namespace launcher

Implement `sandbox.sh` so it launches an arbitrary command in fresh user, UTS, PID, and mount namespaces.

## Preparation and planning

Complete 02.01-02.03 first. This lab combines controls you have observed separately: identity mapping in 02.01, UTS state and argument forwarding in 02.02, and PID/mount/procfs relationships in 02.03. Your job is to order those controls and preserve the caller's interface.

The command must become PID 1, not a child of a shell that unnecessarily remains PID 1. Explain where process replacement is needed before implementing it. An unchanged hostname by itself does not prove shared membership, and a different hostname by itself does not prove separate membership; verify handles as well.

From the course root:

```bash
./lab-start module-02
cd .student/02.lab
pwd
ls -l sandbox.sh
cat sandbox.sh
nano sandbox.sh
```

`lab-start` creates your editable lab copy. The next three commands enter it and confirm the source name; `cat` reads it, and `nano` opens it for editing. Save with `Ctrl-O`, `Enter`, then leave with `Ctrl-X`. Work only in this student copy. The canonical starter is deliberately incomplete:

<!-- source: course/module-02-namespaces/lab/sandbox.sh format=code -->
```bash
#!/bin/sh
set -eu

if [ "$#" -eq 0 ]; then
  echo "usage: $0 COMMAND [ARG ...]" >&2
  exit 2
fi

# Intentional starter flaw: this does not create any isolation.
exec "$@"
```
<!-- /source -->

The interpreter line selects `sh`. `set -eu` enables exit-on-error behavior and errors for unset expansions; neither creates a sandbox. `$#` counts supplied arguments. The `if` block rejects an empty interface, writes usage to stderr with `>&2`, and exits 2. `exec "$@"` preserves arguments and replaces the script, but all namespace setup is missing. Read 02.02's argument-vector exercise before modifying this line.

## Contract

The grader invokes:

```text
NE_EXPECTED_HOSTNAME=randomized-value ./sandbox.sh COMMAND [ARG ...]
```

The launched command must observe:

- the randomized hostname from `NE_EXPECTED_HOSTNAME`;
- a UTS namespace distinct from the grader;
- a PID namespace distinct from the grader, with the command running as namespace PID 1;
- a mount namespace distinct from the grader;
- a procfs that reflects the new PID namespace;
- the command's stdout, stderr, arguments, and exit status.

Do not hard-code a hostname. Do not change the host hostname or mount table. This lab expects an ordinary user in the disposable VM with unprivileged user namespaces enabled.

Useful interfaces have all appeared in the guided lessons. The grader reports properties, not an implementation recipe.

```bash
chmod +x sandbox.sh
./sandbox.sh sh -c 'echo "pid=$$ host=$(hostname)"; ps -o pid,ppid,comm'
../../lab-grade module-02
```

### Test commands, line by line

- `chmod +x sandbox.sh` adds the executable permission needed for the kernel to launch the script directly.
- `./sandbox.sh sh -c '...'` supplies `sh` as the arbitrary command under test; the quoted program observes namespace-local PID, hostname, and procfs state.
- `$$` and `$(hostname)` are intentionally inside single quotes, so the outer shell does not expand them before the sandbox runs.
- `../../lab-grade module-02` invokes the external randomized property grader from the generated workspace.
- The starter's `exec "$@"` preserves the caller's argument vector but creates no namespaces. `$@` is quoted so each original argument stays separate.

## Interpret your result and replay

Run the starter once before editing and record which security properties fail. A compile error is not an observed security denial, and a missing child is not successful containment. After your repair, use both a harmless successful command and a deliberately nonexistent absolute command; the latter must produce a nonzero launcher status.

For the practice grader, read each failed property and revisit its lesson before changing code. Do not alter the grader, canonical files, or generated fixture to force a pass. Passing establishes only the tested contract, not a production-ready sandbox.

From this workspace, `cd ../..` returns to the course root. `./lab-reset module-02` discards this module's student work and generated fixtures after confirmation; copy any notes you want to retain first. Then `./lab-start module-02` creates a fresh randomized attempt. No saved implementation is supplied by this manual.
