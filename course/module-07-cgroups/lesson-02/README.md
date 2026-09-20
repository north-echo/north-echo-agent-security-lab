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

<!-- source: course/module-07-cgroups/lesson-02/memory_hog.py format=code -->
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
<!-- /source -->

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
