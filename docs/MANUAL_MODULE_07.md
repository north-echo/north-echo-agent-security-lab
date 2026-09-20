<!-- source: course/module-07-cgroups/README.md format=markdown -->
# Module 07 - Bound CPU, memory, and process creation

Use cgroup v2 through the ordinary user's delegated systemd manager. Observe effective controller files from inside workloads, trigger bounded pressure, and prove that transient service collection removes the complete process tree.

Play in order: `07.01`, `07.02`, `07.03`, then `module-07`.

Outcomes:

- connect a systemd user unit to its effective cgroup v2 path;
- interpret `cpu.max`, `cpu.stat`, `memory.max`, `memory.events`, `pids.max`, and `pids.events`;
- distinguish throttling, allocation failure/OOM, and PID exhaustion;
- apply limits to a process tree rather than a single PID;
- use bounded transient units whose cleanup is synchronous and ownership-verifiable.

Prerequisites: Modules 01-06, unified cgroup v2, a running delegated systemd user manager, and the `cpu`, `memory`, and `pids` controllers. No root access is used by the exercises.

## Learning route and limits

Earlier controls answered whether an operation may happen. Resource controls answer how much resource the permitted process tree may consume. A file read can be authorized while a computation still exhausts memory or creates too many tasks. These are different failure modes and need different evidence.

07.01 introduces service identity, registered ownership, the delegated user manager, and CPU quota/period observations. 07.02 reads actual memory/swap ceilings before a capped allocator runs and requires specific OOM evidence. 07.03 checks task-controller rejection events, then uses a harmless sleep to practice client timeout versus service cleanup. The independent lab combines resource properties, validation, literal argv, result handling, and exact ownership.

The helpers enforce small input caps even when a property is deliberately omitted. Never replace them with an unbounded stress loop. Do not change host controllers, swap, overcommit, or security-module policy to force a lesson outcome. If the expected runtime prerequisite fails, return to VM preflight.

Before moving on, distinguish throttling, allocation failure/OOM, and task-creation refusal. Explain why a nonzero command status or an absent wildcard listing is insufficient by itself. A timed-out client may leave a separately managed service; retain ownership evidence until collection or verified cleanup is established.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-07-cgroups/lesson-01/README.md format=markdown -->
# 07.01 - Observe an effective CPU quota

## Outcomes and prerequisites

Complete Modules 01-06 first. You will locate a process's cgroup, translate a CPU percentage into a quota/period pair, distinguish throttling from failure, and run a named transient user service without changing global policy.

## Concepts before commands

A **cgroup** groups processes for resource accounting and control. Children begin in their parent's cgroup. A **controller** supplies one kind of resource policy, such as CPU, memory, or task count. These limits compose with earlier namespace and access controls; they do not replace them.

The systemd **user manager** manages services for your ordinary account. The VM's system manager delegates the necessary controllers to it during provisioning. We ask that existing manager to create a **transient service**: a temporary unit configured for this run, not a permanent service file.

`CPUQuota=50%` means at most half of **one CPU's** time over the configured period, shared by the service's tasks. It does not mean half of every CPU in the VM. At a 100 ms period, the kernel representation is `50000 100000`, in microseconds. The first value is quota; the second is period. The word `max` instead of a numeric quota means this cgroup has no local CPU ceiling, though an ancestor may still constrain it.

## Prepare and read the program

From the course root inside the Linux VM:

```bash
./lab-start 07.01
cd .student/07.01
pwd
ls -l inspect_cpu.py
cat inspect_cpu.py
systemctl --user show-environment >/dev/null
```

`lab-start` creates your student copy. `cd`, `pwd`, and `ls` locate it; `cat` displays the source. The last command checks that the user manager is reachable without printing its environment. Failure is a VM/session prerequisite problem: do not substitute `sudo systemd-run`.

```python
#!/usr/bin/env python3
import json
import time
from pathlib import Path

lines = Path("/proc/self/cgroup").read_text().splitlines()
relative = next(line.split("::", 1)[1] for line in lines if line.startswith("0::"))
base = Path("/sys/fs/cgroup") / relative.lstrip("/")
before = (base / "cpu.stat").read_text()
end = time.monotonic() + 1.0
count = 0
while time.monotonic() < end:
    count += 1
after = (base / "cpu.stat").read_text()
print(json.dumps({
    "cgroup": relative,
    "cpu_max": (base / "cpu.max").read_text().strip(),
    "iterations": count,
    "cpu_stat_before": before,
    "cpu_stat_after": after,
}))
```

### Source, line by line

- `json` serializes observations; `time` supplies a monotonic clock; `Path` reads kernel-generated files.
- Reading and splitting `/proc/self/cgroup` gives this process's membership lines. On unified cgroup v2, `0::PATH` identifies the relevant path.
- The generator selects that line, splits once at `::`, and `next` obtains the path. Missing v2 membership is an error, not permission to invent a location.
- `relative.lstrip("/")` removes the initial slash before joining it beneath `/sys/fs/cgroup`. Without that, an absolute right-hand path would replace the prefix.
- The two `cpu.stat` reads sample counters before and after work.
- `time.monotonic() + 1.0` sets a one-second elapsed-time deadline. Wall-clock changes do not extend it.
- The loop performs harmless arithmetic until that deadline. Its iteration count is not a portable benchmark.
- The final JSON includes actual cgroup membership, the effective file's quota/period text, iterations, and both counter snapshots. Requested command flags alone are not the observation.

## Exercise 1 - Establish the unmodified baseline

Predict whether the login shell's cgroup has a local quota, then run:

```bash
python3 inspect_cpu.py > baseline.json
python3 -m json.tool baseline.json
```

The redirection saves this run's JSON; the formatter parses and displays it. Expect a nonzero iteration count and a cgroup path. A usual unconstrained local value is `max 100000`, but retain the value you actually observe. Do not change a parent cgroup to make its output match a sample.

## Exercise 2 - Give each transient unit a verifiable owner

Define this helper in the same guest shell:

```bash
new_cpu_unit() {
  NE_UNIT="north-echo-$(id -u)-07-01-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 07.01 "$NE_UNIT"
}
NE_DESCRIPTION="North Echo 07.01 workspace=$PWD"
```

### Line by line

- A shell function groups commands without running them until its name is called. Its braces delimit the body.
- `id -u` contributes the actual ordinary UID; `secrets.token_hex(4)` contributes eight random hexadecimal characters to avoid reusing another run's name.
- The target-specific prefix and `.service` suffix match the course's ownership contract.
- `register-unit` records this exact future unit in this lesson's runtime registry. It does not create or start the service.
- The description includes the exact prepared workspace. Cleanup verifies the name, description, and delegated cgroup path; a familiar-looking prefix alone is insufficient.
- Keep these variables in this shell. If registration fails, stop and diagnose it before launching.

Now create one bounded service:

```bash
new_cpu_unit
systemd-run --user --wait --pipe --collect --quiet --expand-environment=no \
  --unit="$NE_UNIT" --description="$NE_DESCRIPTION" \
  --property=RuntimeMaxSec=5s --property=TimeoutStopSec=1s \
  --property=MemoryMax=67108864 --property=MemorySwapMax=0 --property=TasksMax=16 \
  --property=CPUQuota=50% --property=CPUQuotaPeriodSec=100ms \
  -- /usr/bin/python3 "$PWD/inspect_cpu.py" > limited.json
python3 -m json.tool limited.json
```

### Line by line

- `--user` selects your delegated manager, not system services.
- `--wait` waits for service completion; `--pipe` connects the workload's streams; `--collect` allows unloading even a failed transient unit. `--quiet` suppresses manager chatter.
- `--expand-environment=no` prevents systemd from expanding dollar-variable syntax inside the command arguments. An argv array alone does not prevent every downstream interpreter from transforming it.
- Unit name and description bind the run to the registered owner.
- The five-second runtime ceiling and one-second stop timeout backstop the one-second program. The memory and task limits keep this observation small.
- The CPU properties specify the quota and its period explicitly.
- `--` ends manager options. The absolute Python and source paths avoid dependence on the service's working directory or command search path.
- Redirection captures workload output for separate inspection. A nonzero launcher status or missing JSON is an error to investigate, not a passing quota test.

Expect `cpu_max` to be `50000 100000`. Under pressure, `nr_throttled` in the after snapshot should increase relative to before. Exact counter values and iterations vary with scheduling; quota enforcement is not a promise of wall-clock responsiveness.

## Exercise 3 - Observe the missing property and repair it

Call `new_cpu_unit` again and repeat the previous command with only the `CPUQuota=50%` property omitted, saving to `missing-quota.json`. Keep the memory, task, and runtime bounds. The program still works, but the local quota should be `max`. If an inherited manager configuration supplies a quota, record it instead of pretending you observed an unlimited case.

Restore the quota, create a fresh unit name, and regenerate `limited.json`. A successful workload alone could not detect the missing control; the effective-state comparison does.

## Checkpoint, collection, and troubleshooting

```bash
python3 -c 'import json; p=json.load(open("limited.json")); assert p["cpu_max"] == "50000 100000"; assert p["iterations"] > 0; print("CPU STATE: PASS")'
systemctl --user show "$NE_UNIT" --property=LoadState
../../lab-cleanup 07.01 --dry-run
../../lab-cleanup 07.01
```

The Python assertions parse actual data rather than searching a matching substring. The exact last unit should report `LoadState=not-found` once collected; `systemctl` may return nonzero for that absent unit. A manager communication error is different from explicit absence. Course cleanup examines every registered unit and retains the registry if ownership cannot be established.

If the user manager is unavailable, return to the documented VM login. If `cpu.max` is missing, stop at preflight rather than mounting a different hierarchy. If the service cannot find the script, inspect the saved absolute path. Never write directly into the parent cgroup or stop units using a wildcard.

Return to the course root with `cd ../..`. `./lab-reset 07.01` deliberately discards this lesson's student files and fixtures after ownership-checked cleanup. Preserve notes first.

## Source truth

The kernel's [cgroup v2 guide](https://docs.kernel.org/admin-guide/cgroup-v2.html) defines membership, hierarchy, `cpu.max`, and counters. In the VM, `man systemd-run` documents waiting, collection, and argument expansion; `man systemd.resource-control` documents CPUQuota and CPUQuotaPeriodSec. The beta baseline uses systemd 259 on Fedora; Ubuntu 24.04's systemd 255 also supports `--expand-environment=no` (added in 254).
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-07-cgroups/lesson-02/README.md format=markdown -->
# 07.02 - Bound memory and observe OOM

## Outcomes and prerequisites

Complete 07.01 first. You will read a workload's actual memory/swap limits, distinguish a small successful allocation from a bounded out-of-memory event, and verify cleanup without mistaking any nonzero exit for successful containment.

## Concepts before commands

A **memory charge** accounts memory to a cgroup. `memory.max` sets its memory ceiling; `memory.swap.max` separately limits swap usage. Swap is storage used to hold memory pages outside RAM. Setting the swap limit to zero prevents this exercise from shifting its pressure into swap.

A mebibyte (MiB) is 1,048,576 bytes. Thus 32 MiB is 33,554,432 bytes. The interpreter, runtime data, and other charged memory share the limit with the lesson's arrays. Asking for 32 MiB of arrays is not the same as keeping the whole process below 32 MiB.

When the kernel cannot reclaim enough charged memory, it may invoke the cgroup's out-of-memory handling. Allocation failure and OOM termination are different outcomes; inspect the evidence before naming one. MemoryMax is not a mathematical promise that a sampled usage counter can never transiently exceed its value. The checkpoint combines the configured kernel limit with the observed OOM result.

## Prepare and read the bounded allocator

From the course root:

```bash
./lab-start 07.02
cd .student/07.02
pwd
ls -l memory_hog.py
cat memory_hog.py
```

These commands prepare, enter, and inspect this lesson's student copy. The misleadingly dramatic filename names a deliberately small teaching allocator, not an unbounded stress tool.

```python
#!/usr/bin/env python3
import json
import sys
import time
from pathlib import Path

if len(sys.argv) != 2 or not sys.argv[1].isdigit() or not 1 <= int(sys.argv[1]) <= 96:
    print("usage: memory_hog.py MIB (integer 1..96)", file=sys.stderr)
    raise SystemExit(2)
mebibytes = int(sys.argv[1])
lines = Path("/proc/self/cgroup").read_text().splitlines()
relative = next(line.split("::", 1)[1] for line in lines if line.startswith("0::"))
base = Path("/sys/fs/cgroup") / relative.lstrip("/")
print(json.dumps({
    "cgroup": relative,
    "memory_max": (base / "memory.max").read_text().strip(),
    "memory_swap_max": (base / "memory.swap.max").read_text().strip(),
    "requested_mib": mebibytes,
}), flush=True)
blocks = []
for index in range(mebibytes):
    blocks.append(bytearray(1024 * 1024))
    if index % 8 == 0:
        print(f"allocated_mib={index + 1}", flush=True)
print("allocation completed", flush=True)
time.sleep(1)
```

### Source, line by line

- The imports provide JSON output, argv/status handling, elapsed waiting, and kernel-file reads.
- The argument guard requires one numeric count from 1 through 96. Invalid inputs stop before allocation. Do not remove that guard or increase the bound.
- The membership lookup is the same `0::PATH` mechanism from 07.01. The program reads its own actual memory and swap limits, not a value supplied by the launcher.
- The first JSON record is flushed before pressure begins so a later killed process does not take its startup evidence with it.
- `blocks = []` retains every allocated object. Without retained references, old objects could be reclaimed and the intended pressure would not accumulate.
- Each `bytearray(1024 * 1024)` creates one initialized MiB. Appending it keeps that allocation alive.
- `index % 8 == 0` prints sparse progress, including the first block. The label is an allocation count, not total resident memory.
- The completion line appears only if the allocation loop finishes. The final one-second sleep is bounded; it does not allocate further memory.

## Exercise 1 - Establish a small functional baseline

Predict whether 16 MiB should fit in the disposable VM's ordinary login environment:

```bash
python3 memory_hog.py 16 > memory-baseline.txt
printf 'baseline status=%s\n' "$?"
cat memory-baseline.txt
```

The first command saves this run's output; the immediate status capture should show 0. The file should contain a startup JSON record, progress, and `allocation completed`. If this small baseline fails, diagnose VM resources before continuing.

## Exercise 2 - Apply a 32 MiB service ceiling

Define a target-specific name/registration helper in this guest shell:

```bash
new_memory_unit() {
  NE_UNIT="north-echo-$(id -u)-07-02-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 07.02 "$NE_UNIT"
}
NE_DESCRIPTION="North Echo 07.02 workspace=$PWD"
```

As in 07.01, the function creates a fresh exact name and records it before launch. The description binds it to this prepared workspace. If registration fails, stop; do not run an unregistered substitute.

Predict which evidence should appear before the process can be killed:

```bash
new_memory_unit
NE_MEMORY_STATUS=0
systemd-run --user --wait --pipe --collect --expand-environment=no \
  --unit="$NE_UNIT" --description="$NE_DESCRIPTION" \
  --property=RuntimeMaxSec=5s --property=TimeoutStopSec=1s \
  --property=MemoryMax=33554432 --property=MemorySwapMax=0 \
  --property=TasksMax=8 --property=CPUQuota=50% \
  -- /usr/bin/python3 "$PWD/memory_hog.py" 96 \
  > memory-output.txt 2> memory-manager.txt || NE_MEMORY_STATUS=$?
printf 'bounded status=%s\n' "$NE_MEMORY_STATUS"
cat memory-output.txt
cat memory-manager.txt
```

### Line by line

- The service uses the ordinary user's manager and an exact registered identity.
- `--wait --pipe --collect` waits for the service and connects output, then permits failed-unit collection. We omit `--quiet` so the manager's result remains visible.
- Runtime, stop, task, and CPU limits backstop this small memory observation.
- MemoryMax is exactly 32 MiB; MemorySwapMax is zero.
- The child requests at most 96 MiB, a fixed synthetic bound. It should not finish under this ceiling.
- The two redirections retain workload stdout and manager/child stderr separately.
- The `||` branch saves failure without changing your shell's `set -e` setting.
- The printed status is necessary but insufficient evidence: a missing script would also fail.

Expected on the course baseline: the initial JSON reports `memory_max` of `33554432` and `memory_swap_max` of `0`; the completion line is absent; the manager reports `oom-kill`; the status is nonzero. Exact progress and peak usage vary with interpreter/runtime overhead.

## Exercise 3 - Compare a missing limit without increasing pressure

Create another fresh unit and repeat the command with only MemoryMax omitted, the request reduced to **16**, and output filenames changed to `missing-limit-output.txt` and `missing-limit-manager.txt`. Keep the other bounds. The workload should complete while reporting no local memory ceiling (`max`), unless a manager default supplies one.

This demonstrates the missing property without asking an unconstrained process to consume more memory. Restore MemoryMax and the bounded 96 MiB request, create a fresh unit, and regenerate the two original evidence files before the checkpoint.

## Checkpoint and troubleshooting

```bash
python3 - "$NE_MEMORY_STATUS" <<'PY'
import json
import sys
from pathlib import Path

output = Path("memory-output.txt").read_text()
initial = json.loads(output.splitlines()[0])
assert initial["memory_max"] == "33554432"
assert initial["memory_swap_max"] == "0"
assert "allocation completed" not in output
assert int(sys.argv[1]) != 0
assert "oom-kill" in Path("memory-manager.txt").read_text()
print("MEMORY LIMIT AND OOM EVIDENCE: PASS")
PY
systemctl --user show "$NE_UNIT" --property=LoadState
../../lab-cleanup 07.02 --dry-run
../../lab-cleanup 07.02
```

The quoted here-document sends the displayed Python program to `python3 -` without shell expansion. The saved status is a separate argument. The assertions require parsed effective limits, incomplete allocation, a failing status, and the manager's specific OOM classification. They do not accept an arbitrary error.

After collection, the last unit should be explicitly not found. Cleanup verifies registered ownership; it never searches for similarly named processes. If the manager is unreachable, the Python file is missing, or the first JSON record is absent, diagnose setup. If the result is `MemoryError` or a runtime timeout rather than `oom-kill`, record that distinct outcome; do not call it the expected OOM observation or raise pressure to force one.

Never change host overcommit, swap, or global OOM settings for this lesson. Return to the course root with `cd ../..`; `./lab-reset 07.02` removes this lesson's work after confirmation. Save notes first.

## Source truth

The kernel's [cgroup v2 memory-controller documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html) defines charging, memory.max, swap limits, and memory.events. The installed `man systemd.resource-control` explains MemoryMax/MemorySwapMax; `man systemd-run` explains result reporting and collection. These are resource controls, not authorization for the data in memory.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-07-cgroups/lesson-03/README.md format=markdown -->
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
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-07-cgroups/lab/README.md format=markdown -->
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
<!-- /source -->
