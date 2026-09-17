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
