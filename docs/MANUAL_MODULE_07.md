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
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-07-cgroups/lesson-01/README.md format=markdown -->
# 07.01 - Observe an effective CPU quota

## Goal

Launch a bounded transient user service, find its actual cgroup from inside the workload, and distinguish a configured percentage from the kernel's quota/period representation.

Complete `inspect_cpu.py` reads `0::PATH` from `/proc/self/cgroup`, anchors that path below `/sys/fs/cgroup`, samples `cpu.stat`, burns CPU for one second, and emits JSON. `time.monotonic()` makes elapsed time independent of wall-clock changes; the loop counter is comparative evidence, not a portable benchmark.

```bash
python3 inspect_cpu.py
systemd-run --user --wait --pipe --collect --quiet \
  --property=CPUQuota=50% -- python3 "$PWD/inspect_cpu.py"
```

### Line by line

- The first run shows the shell's inherited cgroup and commonly reports `cpu.max` as `max 100000`.
- `--user` confines management to the ordinary user's delegated manager.
- `--wait` waits for workload status, `--pipe` preserves output, and `--collect` removes the transient unit and cgroup.
- `CPUQuota=50%` becomes `50000 100000`: 50,000 microseconds of CPU time per 100,000-microsecond period.
- `--` ends systemd-run options; Python and its script remain separate argv elements.

Intentional failure: omit `CPUQuota`. The workload still succeeds, but `cpu.max` reports `max 100000`, proving no CPU ceiling was installed. Restore the property and require `50000 100000`.

## Checkpoint and troubleshooting

```bash
systemd-run --user --wait --pipe --collect --quiet --property=CPUQuota=50% -- python3 "$PWD/inspect_cpu.py" | grep -q '50000 100000'
```

- If the user manager is unavailable, use the documented VM login session; do not switch to system units or `sudo`.
- Quota throttles aggregate CPU time for the cgroup tree; it does not guarantee wall-clock latency or fair scheduling.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-07-cgroups/lesson-02/README.md format=markdown -->
# 07.02 - Bound memory and observe OOM

## Goal

Apply a memory ceiling to an entire transient service and observe a synthetic allocator crossing it without risking the VM.

`memory_hog.py` converts one argument to a count, retains one-megabyte `bytearray` blocks so pages stay charged, prints bounded progress every eight blocks, and sleeps only after allocation completes.

```bash
python3 memory_hog.py 16
set +e
systemd-run --user --wait --pipe --collect --quiet \
  --property=MemoryMax=33554432 --property=MemorySwapMax=0 \
  -- python3 "$PWD/memory_hog.py" 96
status=$?
set -e
printf 'bounded_status=%s\n' "$status"
```

### Line by line

- The 16 MiB baseline should complete normally.
- `MemoryMax=33554432` is an exact 32 MiB cgroup ceiling; `MemorySwapMax=0` prevents the exercise from shifting pressure into swap.
- The 96 MiB request is synthetic and bounded. The kernel kills the charged process tree before it reaches that size.
- `set +e` permits observation of the expected failure; the saved nonzero status is restored to visible evidence before fail-fast mode returns.
- `--collect` removes the failed unit and its cgroup after systemd reports memory peak and service result.

Intentional failure: run the 96 MiB request without `MemoryMax`. It completes and proves observation alone is not enforcement. Restore both memory properties.

## Checkpoint and troubleshooting

```bash
! systemd-run --user --wait --pipe --collect --quiet --property=MemoryMax=33554432 --property=MemorySwapMax=0 -- python3 "$PWD/memory_hog.py" 96
```

- A nonzero result is expected; do not increase the allocation or change host overcommit settings.
- `memory.max` bounds charged memory, while OOM outcome can vary with interpreter startup and kernel accounting. The stable property is containment below the configured ceiling.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-07-cgroups/lesson-03/README.md format=markdown -->
# 07.03 - Bound process-tree growth and collect it

## Goal

Apply a PID ceiling to a process tree, observe a rejected fork, and prove collection removes the transient cgroup.

`fork_pressure.py` resolves its own cgroup, attempts a bounded number of forks, makes each child sleep briefly, reaps every created child, and prints `pids.max` plus `pids.events`. Children use `_exit` so they do not rerun parent cleanup.

```bash
systemd-run --user --wait --pipe --collect --quiet \
  --property=TasksMax=12 -- python3 "$PWD/fork_pressure.py" 64
systemctl --user list-units --all 'run-*.service'
```

### Line by line

- `TasksMax=12` writes `12` to `pids.max` for the whole service tree, including the parent.
- The loop asks for at most 64 children; `fork` fails before that when the cgroup reaches its ceiling.
- Reaping prevents zombies from obscuring the count.
- `pids.events` contains a positive `max` counter after a rejected creation.
- The listing should not contain the collected transient unit. Collection, not killing only one PID, is the cleanup property.

Intentional failure: omit `TasksMax`; all 64 bounded children can be created and `pids.max` is `max`. Restore the ceiling and require fewer than 64 children plus a positive `max` event.

## Checkpoint and troubleshooting

```bash
systemd-run --user --wait --pipe --collect --quiet --property=TasksMax=12 -- python3 "$PWD/fork_pressure.py" 64 | grep -q '"pids_max": "12"'
```

- Never substitute an unbounded fork loop. The fixed upper bound and short sleep make failure recoverable.
- A PID controller bounds task creation; it does not limit CPU or memory, so compose all required controllers.
<!-- /source -->

<!-- PAGEBREAK -->

<!-- source: course/module-07-cgroups/lab/README.md format=markdown -->
# Module 07 independent lab - Bounded transient runner

Implement `resource_runner.py`. The grader invokes:

```text
python3 resource_runner.py SPEC.json RESULT.json
```

The specification contains an absolute-path `command` string array plus integer `memory_max`, `tasks_max`, and `cpu_percent` fields. Your runner must validate conservative bounds, launch the exact argv in a uniquely named transient systemd user service, and set `MemoryMax`, `MemorySwapMax=0`, `TasksMax`, and `CPUQuota`. Use `--wait`, `--pipe`, and `--collect` so completion is synchronous and the cgroup is removed.

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
<!-- /source -->
