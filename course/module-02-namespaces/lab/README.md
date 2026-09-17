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
