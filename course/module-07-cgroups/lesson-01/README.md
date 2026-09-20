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

<!-- source: course/module-07-cgroups/lesson-01/inspect_cpu.py format=code -->
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
<!-- /source -->

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
