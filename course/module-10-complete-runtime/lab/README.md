# Module 10 independent lab - Composed contained runtime

## Assignment and readiness check

Build the single-job launcher practiced in 10.01-10.03. It must retain an approved operation while applying the outer controls and proving owned collection. Do not replace effective observations with input-configuration labels.

Before coding, explain the dependency order, the difference between inner guard and outer launcher, why systemd argv expansion needs explicit treatment, and why an absent exact unit is stronger evidence than requesting collection. Complete the small 0/7/0 worker exercise before progressing to the later batch capstone.

## Prepare and read the starter

From the course root:

```bash
./lab-start module-10
cd .student/10.lab
pwd
ls -l complete_runtime.py
cat complete_runtime.py
nano complete_runtime.py
```

Work only in this prepared copy. Ctrl+O then Enter saves in the default nano configuration; Ctrl+X exits.

<!-- source: course/module-10-complete-runtime/lab/complete_runtime.py format=code -->
```python
#!/usr/bin/env python3
"""Module 10 starter: functional execution without outer runtime controls."""

import json
from pathlib import Path
import subprocess
import sys


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    command = [spec["guard"], spec["allowed_root"], *spec["command"]]
    run = subprocess.run(command, text=True, capture_output=True, check=False, timeout=20)
    Path(sys.argv[2]).write_text(json.dumps({
        "schema": 1, "status": run.returncode, "unit": None,
        "stdout": run.stdout, "stderr": run.stderr, "attestation": None,
    }) + "\n", encoding="utf-8")
    return run.returncode != 0


if __name__ == "__main__":
    raise SystemExit(main())
```
<!-- /source -->

### Starter, line by line

- The imports provide JSON, paths, subprocess execution, and arguments.
- The guard requires a spec and result filename; the starter then parses JSON without the complete validation you must add.
- The command list preserves argv while invoking the supplied guard and workload directly.
- A timeout bounds this incomplete foreground execution, but no cgroup or namespace is created.
- The result records status/output and explicitly has no unit or parsed attestation.
- A nonzero child status makes the starter return nonzero. This is useful baseline behavior, not successful composition.

The starter may perform the guard's inner controls while failing the outer properties. Do not mistake that partial functionality for the assignment being complete.

## Interface and validation contract

The grader invokes:

```text
python3 complete_runtime.py SPEC.json RESULT.json
```

Require exactly `guard`, `allowed_root`, `command`, `memory_max`, `tasks_max`, and `cpu_percent`. Guard/root must be absolute paths of the expected regular-file/directory kind, without a symlink leaf. Treat the guard as trusted operator-provided TCB, not a workload-selectable convenience. Refuse the whole filesystem as an allowed root.

Require nonempty structured string argv without NUL characters, an absolute executable that resolves beneath the allowed root, and actual integer limits: memory 16 MiB through 1 GiB, tasks 4 through 256, CPU 10 through 100 percent. Reject Boolean limits. Invalid input must fail before a result, ownership record, or service is created. These setup paths are trusted for this exercise; do not claim race-free validation against concurrent same-account mutation.

## Launch and collection contract

Record exact unit ownership before launch. In prepared course workspaces, use the course registry with the matching target and workspace description. The isolated external grader copies your single source file into a separate directory; preserve a local ownership record under `.runtime` there, as practiced in 10.03. Use names with the ordinary UID, target, and fresh random suffix; the grader's standalone target is `10.lab`.

Create a transient **user** service with validated CPU/memory/task limits, zero swap, a 100 ms CPU period, a finite runtime backstop, control-group stop semantics, bounded stop time, synchronous waiting, and collection. Disable systemd's own argument environment expansion when promising literal argv.

Within that cgroup create fresh user/network namespaces; then reduce bounding/inheritable/ambient capability sets and set no-new-privileges. Give the final guard/workload a fixed environment without the fake credential. Invoke the trusted guard with the allowed root and separate workload argv. Do not use a shell to reinterpret those arguments.

On normal return, failure, and timeout, inspect the **exact** recorded unit. Before stopping a remaining unit, verify its description and cgroup are owned by the expected delegated user manager. Treat a manager inspection failure as unknown, not absent. Confirm actual unit/cgroup collection before publishing a completed result. Retain ownership evidence and refuse mutation if identity cannot be established.

Write one JSON result with schema 1, workload status, exact unit name, stdout, stderr, and the parsed final-line observation when present. A valid worker exit of 7 must remain 7 in the result and produce a nonzero launcher status. A missing final JSON line need not erase an ordinary worker's status/stderr.

## What the external checks observe

The grader compiles its own static guard and observer, rotates synthetic paths/tokens/credentials, and runs a separate local Unix-socket fixture. It checks:

- effective CPU, memory, swap, and task controller values;
- distinct user/network namespaces and denied AF_INET creation;
- empty capability sets and no-new-privileges;
- allowed/protected file behavior and seccomp mode;
- successful intended Unix-socket operation and fake-credential use by the fixture;
- absence of the known fake credential from observed workload environment/output;
- literal paths, including a systemd-style environment reference;
- ordinary failure status/stderr, invalid-spec refusal, and exact reported-unit/socket absence.

These are finite observations. They do not certify a general parser, a production broker, exclusive access to one Unix socket on ABI 7, durable credential replay state, private PID/mount views, all-channel non-disclosure, or independently bounded outer output capture.

## Map the work to practice

Validation and structured input: Module 04 and 10.03. Resource ownership and timeouts: Module 07 and 10.03. Namespace/privilege ordering: Modules 02-03 and 10.01. Native filesystem/syscall guard: Modules 05-06 and 10.02. Intended broker operation and its limits: Modules 08-09 and 10.03. Failure aggregation and status preservation: Module 04 and the 0/7/0 practice.

Write an explanation of each layer's evidence and one limitation it does not address. The lab does not include a complete launcher implementation.

## Validate, diagnose, and replay

```bash
python3 -m py_compile complete_runtime.py
../../lab-grade module-10
../../lab-grade module-10 --mode exam
```

Compilation checks syntax without creating a service. Practice mode reports failed properties with lesson references; exam mode reduces hints. A failed approved operation must not be “repaired” by removing confinement. Identify which setup/control dependency broke the intended task.

For manual runs, use only generated local fixtures and exact registered ownership. Preview `../../lab-cleanup module-10 --dry-run`, then run `../../lab-cleanup module-10`. Do not kill by prefix, modify host cgroups/firewalls, disable SELinux, or use real credentials.

Save your design notes, return with `cd ../..`, and use `./lab-reset module-10` to discard the working copy and synthetic fixtures after verified cleanup.
