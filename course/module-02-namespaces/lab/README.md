# Module 02 independent lab - Namespace launcher

Implement `sandbox.sh` so it launches an arbitrary command in fresh user, UTS, PID, and mount namespaces.

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
