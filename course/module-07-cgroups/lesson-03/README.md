# 07.03 - Bound process-tree growth and collect it

## Outcomes and prerequisites

Complete 07.01-07.02 first. You will limit task creation, distinguish a rejected fork from other failures, verify exact-unit collection, and practice the distinction between a client timeout and stopping the service it requested.

## Concepts before commands

The cgroup **pids controller** limits tasks, including threads, not merely the number of top-level programs. The parent's task counts against `TasksMax` too. When the controller refuses another creation, `fork` fails rather than producing an extra child. It does not kill already-existing tasks to bring a count down.

A child that exits must still be reaped by its parent. This program saves every child PID and waits for each, connecting to the direct-child lifecycle from 02.03. It never runs an unbounded fork loop.

A transient unit's lifetime is separate from the `systemd-run` client's lifetime. Killing or timing out the client is not proof that the user manager stopped its service. Resource ceilings, a service runtime deadline, and ownership-checked cleanup all have distinct roles.

## Prepare and read the bounded program

From the course root:

```bash
./lab-start 07.03
cd .student/07.03
pwd
ls -l fork_pressure.py
cat fork_pressure.py
```

The commands prepare, locate, and display the student source. If you edit it, use `nano fork_pressure.py`, save with `Ctrl-O`, `Enter`, and leave with `Ctrl-X`. Do not remove the maximum-request guard.

<!-- source: course/module-07-cgroups/lesson-03/fork_pressure.py format=code -->
```python
#!/usr/bin/env python3
import json
import os
import sys
import time
from pathlib import Path

if len(sys.argv) != 2 or not sys.argv[1].isdigit() or not 1 <= int(sys.argv[1]) <= 64:
    print("usage: fork_pressure.py COUNT (integer 1..64)", file=sys.stderr)
    raise SystemExit(2)
requested = int(sys.argv[1])
lines = Path("/proc/self/cgroup").read_text().splitlines()
relative = next(line.split("::", 1)[1] for line in lines if line.startswith("0::"))
base = Path("/sys/fs/cgroup") / relative.lstrip("/")
children = []
failure_errno = None
for _ in range(requested):
    try:
        pid = os.fork()
    except OSError as error:
        failure_errno = error.errno
        break
    if pid == 0:
        time.sleep(0.2)
        os._exit(0)
    children.append(pid)
for pid in children:
    os.waitpid(pid, 0)
print(json.dumps({
    "cgroup": relative,
    "requested": requested,
    "created": len(children),
    "failure_errno": failure_errno,
    "pids_max": (base / "pids.max").read_text().strip(),
    "pids_events": (base / "pids.events").read_text(),
}))
```
<!-- /source -->

### Source, line by line

- Imports provide JSON, process operations, argv, a short sleep, and kernel-file reads.
- The guard accepts only 1 through 64 requested children. Invalid input exits before creating any child.
- The membership lookup identifies this process's own cgroup as in 07.01.
- `children` holds only PIDs actually returned by successful forks. `failure_errno` begins as `None`, which JSON represents as `null`.
- `os.fork()` returns twice: zero in the child, the child's PID in the parent. A failed creation raises `OSError`; the parent records its errno and leaves the creation loop.
- The child sleeps 0.2 seconds and uses `os._exit(0)` to terminate directly. It does not continue into the parent's loop, output, or cleanup.
- The parent appends each child PID, then calls `os.waitpid(pid, 0)` for every one. The zero option requests an ordinary wait for that exact child.
- The output reports requested and created counts, any fork error, the local task ceiling, and the kernel's event counters. A reduced count without a controller event could have another cause.

## Exercise 1 - Apply the task ceiling

Define an exact registered identity for each run:

```bash
new_task_unit() {
  NE_UNIT="north-echo-$(id -u)-07-03-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 07.03 "$NE_UNIT"
}
NE_DESCRIPTION="North Echo 07.03 workspace=$PWD"
```

The name uses the actual UID, this lesson's target, and a random suffix. Registration occurs before launch; the description must continue to identify this exact workspace. Stop if registration fails.

Predict whether a twelve-task ceiling permits twelve new children in addition to their parent:

```bash
new_task_unit
systemd-run --user --wait --pipe --collect --quiet --expand-environment=no \
  --unit="$NE_UNIT" --description="$NE_DESCRIPTION" \
  --property=RuntimeMaxSec=5s --property=TimeoutStopSec=1s \
  --property=MemoryMax=67108864 --property=MemorySwapMax=0 \
  --property=TasksMax=12 --property=CPUQuota=50% \
  -- /usr/bin/python3 "$PWD/fork_pressure.py" 64 > task-output.json
python3 -m json.tool task-output.json
```

### Line by line

- The service is a bounded, named user unit, with the same waiting, stream, collection, and literal-argument controls used earlier.
- Memory, swap, CPU, and runtime ceilings keep this short observation small.
- `TasksMax=12` controls `pids.max` for the entire unit.
- The program may request at most 64 children; the controller should refuse earlier.
- Captured JSON is parsed independently. Expect `pids_max` of `12`, fewer than 64 children, and a positive `max` count in `pids_events`. The parent is included in the limit, so do not expect twelve child slots.

## Exercise 2 - Compare the missing task property and repair it

Create a fresh unit and repeat with only TasksMax omitted, saving to `missing-task-limit.json`. The program's hard cap of 64 remains. A typical service default allows all 64; it may report a finite manager default rather than `max`. Preserve what your VM actually reports.

Restore TasksMax=12, create another fresh unit, and regenerate `task-output.json`. A successful Python exit did not distinguish the two policies; the effective ceiling and rejection event do.

## Exercise 3 - Verify the controller event, not just a configured number

```bash
python3 - <<'PY'
import errno
import json

result = json.load(open("task-output.json"))
events = dict(line.split() for line in result["pids_events"].splitlines())
assert result["pids_max"] == "12"
assert 0 < result["created"] < result["requested"] == 64
assert result["failure_errno"] == errno.EAGAIN
assert int(events["max"]) > 0
print("TASK LIMIT AND REJECTION EVENT: PASS")
PY
systemctl --user show "$NE_UNIT" --property=LoadState
```

The here-document supplies the displayed Python checker without shell expansion. It parses JSON and the event file's key/value lines, checks the actual ceiling, requires a reduced count, verifies the expected resource-unavailable errno, and requires a positive controller event. Each part excludes a different false explanation.

The completed exact unit should be explicitly absent after collection. Do not use a wildcard listing as proof that you identified and checked this particular unit.

## Exercise 4 - Separate client timeout from service cleanup

Use a harmless sleeping service to practice the failure path. No pressure program is needed:

```bash
new_task_unit
NE_CLIENT_STATUS=0
timeout 1s systemd-run --user --wait --pipe --collect --quiet --expand-environment=no \
  --unit="$NE_UNIT" --description="$NE_DESCRIPTION" \
  --property=RuntimeMaxSec=5s --property=TimeoutStopSec=1s \
  --property=KillMode=control-group --property=MemoryMax=33554432 \
  --property=MemorySwapMax=0 --property=TasksMax=4 --property=CPUQuota=50% \
  -- /usr/bin/sleep 4 || NE_CLIENT_STATUS=$?
printf 'client status=%s\n' "$NE_CLIENT_STATUS"
systemctl --user show "$NE_UNIT" --property=LoadState --property=Description --property=ControlGroup
../../lab-cleanup 07.03 --dry-run
../../lab-cleanup 07.03
systemctl --user show "$NE_UNIT" --property=LoadState
```

### Line by line

- `timeout 1s` bounds the client, not the user manager's service. GNU timeout normally reports 124 when its deadline expires.
- The service has an independent five-second runtime backstop, a one-second stop timeout, and whole-cgroup stop behavior.
- `sleep 4` is fixed, local, and harmless. It may still be active when the client exits; depending on elapsed time and manager behavior, it may already have completed by inspection.
- The first `show` reads the exact unit's identity and cgroup without mutating it.
- The dry run plans cleanup against the registry; actual cleanup checks the exact name, workspace description, and delegated cgroup before stopping an active unit.
- The final inspection must show explicit absence. A failed ownership check means stop and investigate; never replace it with a wildcard kill or a global reset-failed command.

The exercise teaches a failure path, not a claim that a timed-out client always leaves a live service. Record the observed state. Both normal collection and a verified stop are valid cleanup outcomes; an unverified assumption is not.

## Bridge to the Python independent lab

You already used `subprocess.run` in Module 04. Its `timeout=` argument raises `subprocess.TimeoutExpired` if that direct child does not finish; the exception is different from a completed child's nonzero status. For a `systemd-run` child, your runner must also handle the separately managed service.

Construct the manager invocation as a list: executable, options, each `--property=NAME=VALUE` string, `--`, then the original command elements. Python's `*command` expands that list's elements into another list without joining or reparsing them. Include `--expand-environment=no`, because the next layer otherwise has its own expansion rules.

Before invoking any service, validate the specification. JSON numbers can become integers, while JSON booleans become Python booleans; `isinstance(True, int)` is true in Python. Reject booleans explicitly for numeric limits. Practice this check in the interpreter:

```bash
python3 -c 'print(isinstance(True, int)); print(isinstance(50, int) and not isinstance(50, bool) and 10 <= 50 <= 100)'
```

The first printed `True` exposes the surprising type relationship. The second demonstrates an actual integer/range check. Use the lab's stated bounds and validate all fields before creating a service or result file.

For cleanup, a generated name is only one part of ownership. The lesson's registry records it before launch; the course cleanup additionally verifies Description and ControlGroup. The independent runner must retain its own exact run identity and verify those properties before requesting a stop. `systemctl --user show EXACT_UNIT --property=LoadState --property=Description --property=ControlGroup` supplies the observations; explicit `not-found` differs from an inspection failure. Do not infer permission to stop anything from a name prefix alone.

## Checkpoint, troubleshooting, and replay

Explain why a fork error plus a positive pids event is stronger evidence than a small child count. Then explain why timing out a launch client is not sufficient cleanup of a service. Repeat the exact-unit inspection after the timeout exercise.

If the child count is zero or errno is unexpected, inspect the service result and parent limits before interpreting it as task-controller enforcement. Never increase the hard cap or run a fork bomb. If cleanup cannot verify ownership, retain the registry and use its diagnostic rather than bypassing the check.

Return with `cd ../..`; `./lab-reset 07.03` removes the lesson workspace and fixtures after verified cleanup. Keep any notes first.

## Source truth

The kernel's [cgroup v2 PID-controller guide](https://docs.kernel.org/admin-guide/cgroup-v2.html) defines pids.max and pids.events. [Python process APIs](https://docs.python.org/3.14/library/os.html) document fork/wait; [subprocess](https://docs.python.org/3.14/library/subprocess.html) documents timeout behavior. In the VM, `man systemd-run`, `man systemd.kill`, and `man timeout` distinguish client lifetime, service lifetime, and whole-cgroup stopping.
