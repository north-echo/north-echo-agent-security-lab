# Module 07 independent lab - Bounded transient runner

Implement `resource_runner.py`, a bounded transient user-service runner.

## Prepare the independent workspace

Complete 07.01-07.03 first. CPU state and user-service options were practiced in 07.01, memory/swap limits and specific failure evidence in 07.02, and task limits, exact ownership, client timeouts, and validation in 07.03. Structured subprocess results come from Module 04.

From the course root:

```bash
./lab-start module-07
cd .student/07.lab
pwd
ls -l resource_runner.py sample-spec.json
cat resource_runner.py
cat sample-spec.json
nano resource_runner.py
```

The commands prepare and enter your student copy, display both interface files, and open the implementation for editing. Save with `Ctrl-O`, `Enter`, and exit with `Ctrl-X`. No C compile is needed. The starter below is deliberately incomplete, not a combined solution:

<!-- source: course/module-07-cgroups/lab/resource_runner.py format=code -->
```python
#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    run = subprocess.run(spec["command"], text=True, capture_output=True, check=False)
    Path(sys.argv[2]).write_text(
        json.dumps({"status": run.returncode, "stdout": run.stdout, "stderr": run.stderr}) + "\n",
        encoding="utf-8",
    )
    return run.returncode != 0


if __name__ == "__main__":
    raise SystemExit(main())
```
<!-- /source -->

Its imports, argv guard, JSON parsing, subprocess call, and JSON result writing use familiar interfaces. The direct subprocess receives no service or cgroup setup. `return run.returncode != 0` becomes a Boolean status: false maps to 0 and true maps to 1. The result field retains the child's more specific code. Preserve that distinction while adding the resource boundary.

## Contract

The grader invokes:

```text
python3 resource_runner.py SPEC.json RESULT.json
```

The specification contains a nonempty `command` string array whose first element is an absolute executable path, plus integer `memory_max`, `tasks_max`, and `cpu_percent` fields. Reject booleans as numeric limits. Accept only 16-256 MiB inclusive for memory (in bytes), 4-64 tasks inclusive, and 10-100 CPU percent inclusive. Validate every field before starting a service or creating the requested result file.

Launch the exact argv in a uniquely named transient systemd user service. Set `MemoryMax`, `MemorySwapMax=0`, `TasksMax`, and `CPUQuota`; use `CPUQuotaPeriodSec=100ms` to make the quota/period contract explicit. Use `--wait`, `--pipe`, and `--collect` so completion is synchronous and failed units can be collected. Include `--expand-environment=no`: even without a shell, systemd otherwise expands variable references in command arguments. Add a bounded service runtime and stop timeout as backstops; they do not replace client timeout handling.

Use the owned naming shape `north-echo-UID-07-lab-RANDOM.service`, with the actual numeric UID and 8-32 lowercase hexadecimal characters in RANDOM. Give it a description identifying this run's workspace, keep an exact ownership record before launch, and verify Description plus the delegated ControlGroup before stopping it. The course cleanup convention is `North Echo 07.lab workspace=ABSOLUTE_WORKSPACE`. A name prefix alone is not proof of ownership. The grader evaluates a copy from a separate directory; derive the active workspace rather than hard-coding your original student path.

The result must be one JSON object containing integer `status` and string `stdout`/`stderr`. Preserve nonzero workload status. If your own timeout or setup fails, stop the exact owned unit before returning. Never use a shell, `sudo`, a system unit, or an unbounded resource value.

The starter runs argv directly, so function succeeds but every effective-limit property fails. The fresh external grader checks the child's real `cpu.max`, `memory.max`, `memory.swap.max`, and `pids.max`, an argv literal, bounded process creation, invalid-spec denial, failure propagation, and post-run unit collection.

```bash
python3 resource_runner.py sample-spec.json result.json
python3 -m json.tool result.json
../../lab-grade module-07
../../lab-grade module-07 --mode exam
```

### Test commands, line by line

- The first command exercises the two-file interface; the checked-in sample uses only `/bin/echo`.
- `json.tool` proves the result is valid JSON rather than trusting display text.
- Practice and exam modes run the same kernel properties with different hint detail.

The lab withholds a complete implementation. Reuse the structured subprocess, unit naming, property ordering, timeout cleanup, and effective-state observations practiced in the guided lessons.

## Verify and replay

Run the starter first and distinguish functional success from missing limits. Then test a successful small command, a command that exits nonzero, malformed limits, and literal arguments containing spaces and dollar-variable syntax. Do not add a shell to make quoting easier.

A passing grader demonstrates its stated kernel observations; it does not exhaustively prove every timeout race or ownership-error path. Explain how your runner handles an inspection error without stopping an unverified unit. Never use wildcard teardown, a system unit, or a global cgroup write.

From the workspace, `cd ../..` returns to the course root. `./lab-reset module-07` discards this module's student work and fixtures after confirmation and owned cleanup. Save notes before replaying. See the guided lessons' kernel and installed systemd references for the mechanisms behind this contract.
